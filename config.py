import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production-xyz123"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # ── Database ──────────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or f"sqlite:///{os.path.join(basedir, 'instance', 'finance.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── ML ────────────────────────────────────────────────────────────────────
    ML_MODELS_PATH = os.path.join(basedir, "app", "ml", "models")

    # ── Upload ────────────────────────────────────────────────────────────────
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
