from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    app_name: str = Field("Cognera", env="APP_NAME")
    version: str = Field("0.2.0", env="APP_VERSION")
    debug: bool = Field(False, env="DEBUG")
    database_url: str = Field("postgresql+psycopg://user:password@localhost:5432/cognera", env="DATABASE_URL")
    cors_origins: List[str] = Field(default_factory=lambda: ["*"], env="CORS_ORIGINS")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
