"""
Configuration management for ORBCOMM Service Tracker
Supports multiple environments: development, staging, production
"""

import os
from pathlib import Path
from typing import Optional


class Config:
    """Base configuration with common settings"""

    # Application info
    APP_NAME = "ORBCOMM Service Tracker"
    APP_VERSION = "1.1.0"

    # Flask settings
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    DEBUG = False
    TESTING = False

    # Data directory
    ORBCOMM_DATA_DIR = os.environ.get(
        "ORBCOMM_DATA_DIR", str(Path.home() / ".orbcomm")
    )

    # Database
    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH", str(Path(ORBCOMM_DATA_DIR) / "tracker.db")
    )

    # Gmail API settings
    GMAIL_CREDENTIALS_PATH = os.environ.get(
        "GMAIL_CREDENTIALS_PATH", str(Path(ORBCOMM_DATA_DIR) / "credentials.json")
    )
    GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

    # Email processing
    EMAIL_ARCHIVE_DAYS = int(os.environ.get("EMAIL_ARCHIVE_DAYS", "180"))
    EMAIL_BATCH_SIZE = int(os.environ.get("EMAIL_BATCH_SIZE", "100"))

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_DIR = os.environ.get("LOG_DIR", str(Path(ORBCOMM_DATA_DIR) / "logs"))

    # Flask-CORS
    CORS_ENABLED = os.environ.get("CORS_ENABLED", "true").lower() == "true"
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

    # Server settings
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5000"))
    WORKERS = int(os.environ.get("WORKERS", "4"))

    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

    # Rate limiting
    RATELIMIT_ENABLED = os.environ.get("RATELIMIT_ENABLED", "true").lower() == "true"
    RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "100 per hour")
    RATELIMIT_STORAGE_URL = os.environ.get("RATELIMIT_STORAGE_URL", "memory://")

    # Monitoring
    METRICS_ENABLED = os.environ.get("METRICS_ENABLED", "false").lower() == "true"
    HEALTH_CHECK_ENABLED = True

    # Scheduler
    SCHEDULER_ENABLED = os.environ.get("SCHEDULER_ENABLED", "true").lower() == "true"
    SYNC_SCHEDULE_TIME = os.environ.get("SYNC_SCHEDULE_TIME", "08:00")

    @staticmethod
    def init_app(app):
        """Initialize application with this configuration"""
        # Create necessary directories
        os.makedirs(Config.ORBCOMM_DATA_DIR, exist_ok=True)
        os.makedirs(Config.LOG_DIR, exist_ok=True)


class DevelopmentConfig(Config):
    """Development environment configuration"""

    DEBUG = True
    TESTING = False

    # Less restrictive CORS for development
    CORS_ORIGINS = "*"

    # Development-specific settings
    SECRET_KEY = "dev-secret-key-not-for-production"
    SESSION_COOKIE_SECURE = False

    # More verbose logging
    LOG_LEVEL = "DEBUG"

    # Disable rate limiting in development
    RATELIMIT_ENABLED = False


class TestingConfig(Config):
    """Testing environment configuration"""

    TESTING = True
    DEBUG = True

    # Use in-memory database for tests
    DATABASE_PATH = ":memory:"

    # Disable external services
    SCHEDULER_ENABLED = False
    RATELIMIT_ENABLED = False

    # Test-specific settings
    SECRET_KEY = "test-secret-key"
    SESSION_COOKIE_SECURE = False


class StagingConfig(Config):
    """Staging environment configuration"""

    DEBUG = False
    TESTING = False

    # Staging-specific settings
    LOG_LEVEL = "INFO"

    # Enable monitoring
    METRICS_ENABLED = True

    # Staging may have different CORS requirements
    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS", "https://staging.orbcomm-tracker.example.com"
    )


class ProductionConfig(Config):
    """Production environment configuration"""

    DEBUG = False
    TESTING = False

    # Production security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

    # Production logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARNING")

    # Enable monitoring
    METRICS_ENABLED = True

    # Strict CORS
    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS", "https://orbcomm-tracker.example.com"
    )

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # Production-specific initialization
        # Example: Setup error logging to external service
        import logging
        from logging.handlers import SysLogHandler

        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


class DockerConfig(Config):
    """Docker container configuration"""

    # Docker-specific paths
    ORBCOMM_DATA_DIR = "/app/data"
    DATABASE_PATH = "/app/data/tracker.db"
    LOG_DIR = "/app/logs"


# Configuration dictionary
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "staging": StagingConfig,
    "production": ProductionConfig,
    "docker": DockerConfig,
    "default": DevelopmentConfig,
}


def get_config(env: Optional[str] = None) -> Config:
    """
    Get configuration based on environment

    Args:
        env: Environment name (development, testing, staging, production)
             If None, uses FLASK_ENV or defaults to 'development'

    Returns:
        Config class for the specified environment
    """
    if env is None:
        env = os.environ.get("FLASK_ENV", "development")

    return config.get(env, config["default"])
