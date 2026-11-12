import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import auth, complaints, dashboard
from app.services.seed import seed_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bsphcl")

app = FastAPI(
    title="BSPHCL IT Helpdesk Management System",
    description="REST API for the Bihar State Power (Holding) Company Ltd. IT Cell helpdesk.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(complaints.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    seed_data()
    logger.info("Connected to Supabase PostgreSQL at %s", settings.safe_display_url)


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
