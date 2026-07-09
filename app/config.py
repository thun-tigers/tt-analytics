import os
from pathlib import Path


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("SQLALCHEMY_DATABASE_URI")
        or os.environ.get("DATABASE_URL")
        or "postgresql+psycopg://tt_analytics:tt_analytics_password@tt-postgres-analytics:5432/tt_analytics"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    AUTH_BASE_URL = os.environ.get("AUTH_BASE_URL", "http://localhost:8085").rstrip("/")
    SSO_SHARED_SECRET = os.environ.get("SSO_SHARED_SECRET", SECRET_KEY)
    SSO_EXPECTED_AUDIENCE = os.environ.get("SSO_EXPECTED_AUDIENCE", "tt-analytics")
    SSO_REPLAY_STORAGE_URI = os.environ.get("SSO_REPLAY_STORAGE_URI", "")
    SSO_REPLAY_TTL_SECONDS = int(os.environ.get("SSO_REPLAY_TTL_SECONDS", 300))
    SSO_AUTO_PROVISION_USERS = os.environ.get("SSO_AUTO_PROVISION_USERS", "true").lower() == "true"
    SSO_SYNC_ROLE = os.environ.get("SSO_SYNC_ROLE", "true").lower() == "true"
    TT_MEMBERS_INTERNAL_URL = os.environ.get("TT_MEMBERS_INTERNAL_URL", "http://tt-members:5000")
    INTERNAL_API_SECRET = os.environ.get("INTERNAL_API_SECRET") or SSO_SHARED_SECRET

    AUTO_CREATE_DB = os.environ.get("AUTO_CREATE_DB", "true").lower() == "true"
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
    UPLOAD_ROOT = os.environ.get("UPLOAD_ROOT", str(Path("instance") / "uploads"))
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 2 * 1024 * 1024 * 1024))
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_FILE_POLL_SECONDS = int(os.environ.get("GEMINI_FILE_POLL_SECONDS", 5))
    GEMINI_FILE_POLL_TIMEOUT_SECONDS = int(os.environ.get("GEMINI_FILE_POLL_TIMEOUT_SECONDS", 300))
    GEMINI_MAX_RETRIES = int(os.environ.get("GEMINI_MAX_RETRIES", 8))
    GEMINI_RETRY_BUFFER_SECONDS = int(os.environ.get("GEMINI_RETRY_BUFFER_SECONDS", 5))
    GEMINI_RETRY_DEFAULT_SECONDS = int(os.environ.get("GEMINI_RETRY_DEFAULT_SECONDS", 60))
    ANALYSIS_CONCURRENCY = max(1, int(os.environ.get("ANALYSIS_CONCURRENCY", 2)))
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
