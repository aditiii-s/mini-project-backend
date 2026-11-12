import os
from functools import lru_cache
from urllib.parse import quote_plus, urlparse

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application configuration read from environment variables.

    The database is Supabase (managed PostgreSQL). Provide the connection string
    as DATABASE_URL - copy it from the Supabase dashboard under
    Project Settings -> Database -> Connection string -> URI.

    As a convenience, the individual SUPABASE_DB_* variables are also accepted
    and assembled into a URL when DATABASE_URL is not set.
    """

    DATABASE_URL: str = os.getenv("DATABASE_URL", "").strip()

    DB_HOST: str = os.getenv("SUPABASE_DB_HOST", "").strip()
    DB_PORT: str = os.getenv("SUPABASE_DB_PORT", "5432").strip()
    DB_NAME: str = os.getenv("SUPABASE_DB_NAME", "postgres").strip()
    DB_USER: str = os.getenv("SUPABASE_DB_USER", "postgres").strip()
    DB_PASSWORD: str = os.getenv("SUPABASE_DB_PASSWORD", "")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))

    CORS_ORIGINS: list = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if o.strip()
    ]

    @property
    def database_url(self) -> str:
        """SQLAlchemy URL, always normalised to the psycopg (v3) driver."""
        url = self.DATABASE_URL
        if not url:
            if not self.DB_HOST:
                raise RuntimeError(
                    "No database configured. Set DATABASE_URL in backend/.env to your "
                    "Supabase connection string (Project Settings -> Database -> "
                    "Connection string -> URI)."
                )
            url = (
                f"postgresql://{self.DB_USER}:{quote_plus(self.DB_PASSWORD)}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )

        # Accept the plain URI that Supabase shows and the postgres:// alias.
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://") :]
        if url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://") :]
        return url

    @property
    def uses_transaction_pooler(self) -> bool:
        """Supabase's transaction pooler (port 6543) runs PgBouncer in transaction
        mode, which cannot hold server-side prepared statements or a client pool."""
        try:
            return urlparse(self.database_url).port == 6543
        except (ValueError, RuntimeError):
            return False

    @property
    def safe_display_url(self) -> str:
        """The connection target without the password, for logs and errors."""
        try:
            parsed = urlparse(self.database_url)
        except (ValueError, RuntimeError):
            return "(unset)"
        host = parsed.hostname or "?"
        port = parsed.port or 5432
        return f"{host}:{port}{parsed.path or ''}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
