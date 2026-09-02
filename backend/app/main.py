from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.api.router import api_router
from app.api.routes.contact import limiter, rate_limit_exceeded_handler
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url=None,
    )
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=[
            "Content-Type",
            "X-User-Id",
            "X-User-Name",
            "X-User-Email",
            "X-User-Email-Verified",
            "X-Auth-Provider",
            "X-Auth-Provider-Account-Id",
        ],
    )
    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_app()
