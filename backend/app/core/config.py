"""
Application Configuration Module

This module handles all environment variable configuration using Pydantic BaseSettings.
It provides type-safe access to configuration values with validation.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator, HttpUrl


class Settings(BaseSettings):
    """
    Application Settings loaded from environment variables.
    
    Uses Pydantic BaseSettings for automatic validation and type conversion.
    Environment variables can be loaded from .env file or system environment.
    """

    # ========================================================================
    # Application Settings
    # ========================================================================
    app_name: str = Field(default="XTeam", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # ========================================================================
    # Server Configuration
    # ========================================================================
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=True, description="Auto-reload on code changes")

    # ========================================================================
    # Database Configuration
    # ========================================================================
    database_url: str = Field(
        default="sqlite+aiosqlite:///./xteam.db",
        description="Database URL (SQLite for development)"
    )
    database_echo: bool = Field(default=False, description="Echo SQL queries")
    database_pool_size: int = Field(default=20, description="Database connection pool size")
    database_max_overflow: int = Field(default=10, description="Database max overflow connections")

    # ========================================================================
    # Redis Configuration
    # ========================================================================
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for general cache"
    )
    redis_cache_url: str = Field(
        default="redis://localhost:6379/1",
        description="Redis URL for cache operations"
    )
    redis_queue_url: str = Field(
        default="redis://localhost:6379/2",
        description="Redis URL for task queue"
    )

    # ========================================================================
    # JWT Authentication
    # ========================================================================
    secret_key: str = Field(
        default="your-super-secret-key-change-this-in-production",
        description="Secret key for JWT signing"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration in minutes")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiration in days")

    # ========================================================================
    # CORS Configuration
    # ========================================================================
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow credentials in CORS")
    cors_allow_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        description="Allowed HTTP methods"
    )
    cors_allow_headers: List[str] = Field(default=["*"], description="Allowed headers")

    # ========================================================================
    # LLM API Configuration
    # ========================================================================
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-4", description="OpenAI model name")
    openai_temperature: float = Field(default=0.7, description="OpenAI temperature")
    openai_max_tokens: int = Field(default=2000, description="OpenAI max tokens")

    # Azure OpenAI
    azure_openai_api_key: Optional[str] = Field(default=None, description="Azure OpenAI API key")
    azure_openai_endpoint: Optional[str] = Field(default=None, description="Azure OpenAI endpoint")
    azure_openai_deployment_name: Optional[str] = Field(default=None, description="Azure OpenAI deployment name")
    azure_openai_api_version: str = Field(default="2024-02-15-preview", description="Azure OpenAI API version")

    # Groq
    groq_api_key: Optional[str] = Field(default=None, description="Groq API key")

    # Ollama (Local LLM)
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama base URL")
    ollama_model: str = Field(default="llama2", description="Ollama model name")

    # ========================================================================
    # MetaGPT Configuration
    # ========================================================================
    metagpt_workspace: str = Field(
        default="/workspaces/XTeam/backend/workspaces",
        description="MetaGPT workspace directory"
    )
    metagpt_log_level: str = Field(default="INFO", description="MetaGPT log level")
    metagpt_enable_streaming: bool = Field(default=True, description="Enable MetaGPT streaming")

    # ========================================================================
    # File Storage Configuration
    # ========================================================================
    upload_dir: str = Field(
        default="/workspaces/XTeam/backend/uploads",
        description="Upload directory path"
    )
    max_upload_size_mb: int = Field(default=100, description="Max upload size in MB")
    allowed_file_extensions: List[str] = Field(
        default=[".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml", ".md", ".txt", ".html", ".css"],
        description="Allowed file extensions"
    )

    # ========================================================================
    # Email Configuration
    # ========================================================================
    smtp_server: str = Field(default="smtp.gmail.com", description="SMTP server")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_username: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    smtp_from_email: str = Field(default="noreply@xteam.ai", description="From email address")
    smtp_from_name: str = Field(default="XTeam", description="From name")

    # ========================================================================
    # Deployment Configuration
    # ========================================================================
    vercel_token: Optional[str] = Field(default=None, description="Vercel API token")
    vercel_project_id: Optional[str] = Field(default=None, description="Vercel project ID")

    netlify_token: Optional[str] = Field(default=None, description="Netlify API token")
    netlify_site_id: Optional[str] = Field(default=None, description="Netlify site ID")

    docker_registry_url: str = Field(default="docker.io", description="Docker registry URL")
    docker_registry_username: Optional[str] = Field(default=None, description="Docker registry username")
    docker_registry_password: Optional[str] = Field(default=None, description="Docker registry password")

    # ========================================================================
    # Monitoring & Analytics
    # ========================================================================
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN")
    sentry_environment: str = Field(default="development", description="Sentry environment")
    sentry_traces_sample_rate: float = Field(default=1.0, description="Sentry traces sample rate")

    # ========================================================================
    # Feature Flags
    # ========================================================================
    enable_websocket_streaming: bool = Field(default=True, description="Enable WebSocket streaming")
    enable_agent_persistence: bool = Field(default=True, description="Enable agent persistence")
    enable_code_execution: bool = Field(default=False, description="Enable code execution")
    enable_deployment: bool = Field(default=False, description="Enable deployment features")

    # ========================================================================
    # Security
    # ========================================================================
    ssl_certfile: Optional[str] = Field(default=None, description="SSL certificate file path")
    ssl_keyfile: Optional[str] = Field(default=None, description="SSL key file path")
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests_per_minute: int = Field(default=60, description="Rate limit requests per minute")

    # ========================================================================
    # Celery Configuration
    # ========================================================================
    celery_broker_url: str = Field(
        default="redis://localhost:6379/2",
        description="Celery broker URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend URL"
    )
    celery_task_serializer: str = Field(default="json", description="Celery task serializer")
    celery_result_serializer: str = Field(default="json", description="Celery result serializer")
    celery_accept_content: List[str] = Field(default=["json"], description="Celery accepted content types")
    celery_timezone: str = Field(default="UTC", description="Celery timezone")

    # ========================================================================
    # Validators
    # ========================================================================

    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("allowed_file_extensions", pre=True)
    def parse_allowed_extensions(cls, v):
        """Parse allowed file extensions from comma-separated string or list."""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v

    @validator("cors_allow_methods", pre=True)
    def parse_cors_methods(cls, v):
        """Parse CORS methods from comma-separated string or list."""
        if isinstance(v, str):
            return [method.strip() for method in v.split(",")]
        return v

    @validator("openai_temperature")
    def validate_temperature(cls, v):
        """Validate temperature is between 0 and 2."""
        if not 0 <= v <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        return v

    @validator("database_pool_size")
    def validate_pool_size(cls, v):
        """Validate pool size is positive."""
        if v <= 0:
            raise ValueError("Database pool size must be positive")
        return v

    @validator("port")
    def validate_port(cls, v):
        """Validate port is in valid range."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @validator("access_token_expire_minutes")
    def validate_token_expiry(cls, v):
        """Validate token expiry is positive."""
        if v <= 0:
            raise ValueError("Token expiry must be positive")
        return v

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from .env


# Create global settings instance
settings = Settings()
