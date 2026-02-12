from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # fal.ai
    fal_key: str = ""
    fal_model: str = "fal-ai/flux/dev"

    # Anthropic
    anthropic_api_key: str = ""

    # Firebase
    firebase_service_account_path: str = "./firebase-service-account.json"
    firebase_project_id: str = ""

    # Cloudflare R2
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "tailormade-books"
    r2_public_url: str = ""

    # App
    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"
    secret_key: str = "dev-secret-change-in-prod"

    # Rate limits
    free_daily_limit: int = 1
    premium_daily_limit: int = 10

    # Redis
    redis_host: str = ""
    redis_port: int = 6379
    redis_password: str = ""
    redis_username: str = "default"

    # Sentry
    sentry_dsn: str = ""
    sentry_traces_sample_rate: float = 1.0

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def redis_url(self) -> str:
        """Build Redis URL from components."""
        if not self.redis_host:
            return ""
        auth = ""
        if self.redis_password:
            auth = f":{self.redis_password}@"
            if self.redis_username and self.redis_username != "default":
                auth = f"{self.redis_username}:{self.redis_password}@"
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/0"

    def validate_for_production(self) -> None:
        """Raise if critical settings are missing or insecure in production."""
        if not self.is_production:
            return
        if self.secret_key == "dev-secret-change-in-prod":
            raise ValueError(
                "SECRET_KEY must be changed in production. "
                "Generate one with: openssl rand -hex 32"
            )
        if not self.fal_key:
            raise ValueError("FAL_KEY is required in production")
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required in production")


@lru_cache
def get_settings() -> Settings:
    return Settings()
