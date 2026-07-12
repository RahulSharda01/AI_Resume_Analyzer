import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration for the Flask application."""

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")

    # Default to SQLite for local development while remaining easy to switch to MySQL later.
    use_mysql = os.getenv("USE_MYSQL", "").lower() in {"1", "true", "yes"}
    database_url = os.getenv("DATABASE_URL")
    if use_mysql and database_url:
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB upload limit
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "resumes")


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
