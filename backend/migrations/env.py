from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.contact.models import ContactSubmissionRecord  # noqa: F401
from app.core.config import get_settings
from app.core.database import Base
from app.documents.classification.models import DocumentClassificationRecord  # noqa: F401
from app.documents.models import DocumentRecord  # noqa: F401
from app.property.models import AnalysisCaseRecord, UserRecord  # noqa: F401
from app.property.normalization.dpe import DpeExtractionRecord  # noqa: F401
from app.property.normalization.structured import StructuredExtractionRecord  # noqa: F401
from app.risks.models.findings import RiskFindingRecord  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

database_url = get_settings().database_url
if database_url is not None:
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
