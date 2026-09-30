"""Shared admission and cooldown across workers, without sleeping inside requests."""

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from random import uniform
from typing import Any
from uuid import uuid4

from openai import APIConnectionError, APIStatusError
from sqlalchemy import JSON, String, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.config import Settings
from app.core.database import Base


class LLMRateBudgetRecord(Base):
    __tablename__ = "llm_rate_budgets"
    model: Mapped[str] = mapped_column(String(100), primary_key=True)
    state: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class DeferredLLMCall(RuntimeError):
    def __init__(self, retry_at: datetime, reason: str, *, attempted: bool = False) -> None:
        super().__init__(reason)
        self.retry_at = retry_at
        self.reason = reason
        self.attempted = attempted


def utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def retryable_error(error: BaseException) -> BaseException | None:
    """Domain adapters wrap SDK errors, so inspect the explicit exception chain."""
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, (DeferredLLMCall, APIConnectionError, TimeoutError)):
            return current
        if isinstance(current, APIStatusError):
            body = current.body if isinstance(current.body, dict) else {}
            if body.get("code") in {"insufficient_quota", "billing_hard_limit_reached"}:
                return None
            if current.status_code in {408, 409, 429} or current.status_code >= 500:
                return current
            return None
        current = current.__cause__
    return None


def retry_at_for(error: BaseException, attempt: int, now: datetime) -> datetime:
    if isinstance(error, DeferredLLMCall):
        return error.retry_at
    delay = min(300, 5 * 2 ** max(0, attempt - 1))
    if isinstance(error, APIStatusError):
        headers = error.response.headers
        try:
            if value := headers.get("retry-after"):
                try:
                    delay = max(delay, float(value))
                except ValueError:
                    delay = max(delay, (utc(parsedate_to_datetime(value)) - now).total_seconds())
            if value := headers.get("retry-after-ms"):
                delay = max(delay, float(value) / 1000)
        except (ValueError, TypeError, OverflowError):
            pass
    return now + timedelta(seconds=delay + uniform(0.5, 2.5))


class LLMRateBudget:
    def __init__(self, session: Session, settings: Settings, model: str) -> None:
        self.session = session
        self.settings = settings
        self.model = model

    def _locked_record(self) -> LLMRateBudgetRecord:
        insert = (
            pg_insert if self.session.get_bind().dialect.name == "postgresql" else sqlite_insert
        )
        self.session.execute(
            insert(LLMRateBudgetRecord)
            .values(model=self.model, state={})
            .on_conflict_do_nothing(index_elements=["model"])
        )
        record = self.session.scalar(
            select(LLMRateBudgetRecord)
            .where(LLMRateBudgetRecord.model == self.model)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        assert record is not None
        return record

    def reserve(self, tokens: int, now: datetime | None = None) -> str:
        now = now or datetime.now(UTC)
        record = self._locked_record()
        state = dict(record.state)
        requests = [item for item in state.get("requests", []) if item["at"] > now.timestamp() - 60]
        slots = {key: end for key, end in state.get("slots", {}).items() if end > now.timestamp()}
        cooldown = state.get("cooldown", 0)
        retry = now.timestamp()
        reason = "capacity"
        if cooldown > retry:
            retry, reason = cooldown, "rate_limit"
        if len(slots) >= self.settings.openai_max_concurrency:
            # Check promptly again; the active call usually finishes before its lease.
            retry = max(retry, now.timestamp() + 3)
        if len(requests) >= self.settings.openai_requests_per_minute or (
            sum(item["tokens"] for item in requests) + tokens
            > self.settings.openai_tokens_per_minute
        ):
            retry = max(retry, requests[0]["at"] + 60 if requests else now.timestamp() + 60)
            reason = "rate_limit"
        if tokens > self.settings.openai_tokens_per_minute:
            self.session.rollback()
            raise ValueError("This request exceeds the configured token budget")
        if retry > now.timestamp():
            self.session.commit()
            raise DeferredLLMCall(datetime.fromtimestamp(retry, UTC), reason)
        reservation = str(uuid4())
        requests.append({"id": reservation, "at": now.timestamp(), "tokens": tokens})
        slots[reservation] = now.timestamp() + self.settings.openai_timeout_seconds + 10
        record.state = {**state, "requests": requests, "slots": slots}
        self.session.commit()
        return reservation

    def finish(self, reservation: str, actual_tokens: int | None = None) -> None:
        record = self._locked_record()
        state = dict(record.state)
        slots = dict(state.get("slots", {}))
        slots.pop(reservation, None)
        requests = [dict(item) for item in state.get("requests", [])]
        if actual_tokens is not None:
            for item in requests:
                if item["id"] == reservation:
                    item["tokens"] = actual_tokens
        record.state = {**state, "slots": slots, "requests": requests}
        self.session.commit()

    def cooldown(self, retry_at: datetime) -> None:
        record = self._locked_record()
        record.state = {
            **record.state,
            "cooldown": max(record.state.get("cooldown", 0), retry_at.timestamp()),
        }
        self.session.commit()

    async def call[T](
        self,
        operation: Callable[[], Awaitable[T]],
        *,
        tokens: int,
        on_admitted: Callable[[], None] | None = None,
    ) -> T:
        reservation = self.reserve(tokens)
        actual_tokens = None
        try:
            if on_admitted is not None:
                on_admitted()
            result = await operation()
            actual_tokens = getattr(result, "input_tokens", 0) + getattr(result, "output_tokens", 0)
            return result
        except Exception as error:
            retryable = retryable_error(error)
            if retryable is not None:
                retry_at = retry_at_for(retryable, 1, datetime.now(UTC))
                if isinstance(retryable, APIStatusError):
                    self.cooldown(retry_at)
                raise DeferredLLMCall(retry_at, "rate_limit", attempted=True) from error
            raise
        finally:
            self.finish(reservation, actual_tokens)


class BudgetedStructuredClient:
    def __init__(self, client: Any, budget: LLMRateBudget) -> None:
        self.client = client
        self.budget = budget

    async def parse(self, **kwargs: Any) -> Any:
        # Conservative French text estimate plus the bounded output allowance.
        tokens = len(kwargs["user_content"].encode("utf-8")) // 2 + 17000
        return await self.budget.call(lambda: self.client.parse(**kwargs), tokens=tokens)
