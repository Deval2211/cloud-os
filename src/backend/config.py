"""
Configuration management for Cloud OS Backend
"""
from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # ===========================================================================
    # Server Configuration
    # ===========================================================================
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"

    # ===========================================================================
    # Database Configuration
    # ===========================================================================
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/cloud_os"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False

    # ===========================================================================
    # Redis Configuration
    # ===========================================================================
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_CACHE_TTL: int = 3600

    # ===========================================================================
    # MinIO / S3 Configuration
    # ===========================================================================
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "minioadmin"
    MINIO_USE_SSL: bool = False
    CHECKPOINT_BUCKET: str = "cloud-os-checkpoints"
    CHECKPOINT_RETENTION_DAYS: int = 30

    # ===========================================================================
    # Authentication Configuration
    # ===========================================================================
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRATION_DAYS: int = 30

    # GitHub OAuth
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_OAUTH_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/github/callback"

    # ===========================================================================
    # Provider Configuration
    # ===========================================================================
    ENABLED_PROVIDERS: List[str] = ["local_docker"]
    RUNPOD_API_KEY: str = ""
    VASTAI_API_KEY: str = ""

    # ===========================================================================
    # LLM Configuration
    # ===========================================================================
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    DEFAULT_LLM_MODEL: str = "gpt-4"
    LLM_TEMPERATURE: float = 0.3

    # ===========================================================================
    # Email Configuration
    # ===========================================================================
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@cloud-os.example.com"

    # ===========================================================================
    # Monitoring & Logging
    # ===========================================================================
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None

    # ===========================================================================
    # Feature Flags
    # ===========================================================================
    ENABLE_WORKFLOW_ENGINE: bool = True
    ENABLE_AI_ASSISTANT: bool = True
    ENABLE_COLLABORATION: bool = False
    ENABLE_EDGE_AGENTS: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
