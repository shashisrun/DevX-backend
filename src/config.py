from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = Field(default="postgresql://user:password@localhost:5432/devinx", env="DATABASE_URL")
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    FASTAPI_HOST: str = Field(default="0.0.0.0", env="FASTAPI_HOST")
    FASTAPI_PORT: int = Field(default=8000, env="FASTAPI_PORT")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    WEBSOCKET_URL: str = Field(default="ws://localhost:8000/ws", env="WEBSOCKET_URL")
    REQUIRE_APPROVAL_PLANNING: bool = Field(default=False, env="REQUIRE_APPROVAL_PLANNING")
    basic_auth_enabled: bool = Field(default=False)
    basic_auth_user: str = Field(default="admin")
    basic_auth_pass: str = Field(default="change-me")
    openai_api_key: str = Field(default="")
    groq_api_key: str = Field(default="")

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
