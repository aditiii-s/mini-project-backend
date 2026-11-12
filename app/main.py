import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import auth, complaints, dashboard, extras
from app.services.seed import seed_data
from app.services.seed_extras import seed_extras

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bsphcl")

app = FastAPI(
    title="BSPHCL IT Helpdesk Management System",
    description="REST API for the Bihar State Power (Holding) Company Ltd. IT Cell helpdesk.",
    version="1.0.0",
)

cors_kwargs = {
    "allow_origins": settings.CORS_ORIGINS,
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
if settings.CORS_ORIGIN_REGEX:
    cors_kwargs["allow_origin_regex"] = settings.CORS_ORIGIN_REGEX

app.add_middleware(CORSMiddleware, **cors_kwargs)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(complaints.router)
app.include_router(extras.service_router)
app.include_router(extras.announcement_router)
app.include_router(extras.notification_router)
app.include_router(extras.kb_router)


@app.on_event("startup")
def on_startup() -> None:
    if settings.RUN_DB_INIT:
        init_db()
        seed_data()
        seed_extras()
        logger.info("Connected to Supabase PostgreSQL at %s", settings.safe_display_url)
    else:
        # Serverless deployment: the schema already exists, so skip the DDL and
        # seed pass that would otherwise run on every cold start.
        logger.info(
            "RUN_DB_INIT is off - skipping schema setup. Using %s",
            settings.safe_display_url,
        )


@app.get("/", tags=["Health"])
def root():
    return {
        "name": "BSPHCL IT Helpdesk Management System",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/api/health", tags=["Health"])
def health():
    from sqlalchemy import text

    from app.database import engine

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": settings.safe_display_url}
    except Exception as exc:  # pragma: no cover
        return {"status": "error", "detail": str(exc)}
