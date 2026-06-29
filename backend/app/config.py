from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://nyubites:changeme@localhost:5432/nyubites"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Refresh tokens (opaque, stored in Redis)
    refresh_token_expire_days: int = 30

    # Email verification token TTL
    verification_token_expire_hours: int = 24

    # Password reset token TTL
    reset_token_expire_minutes: int = 60

    # Email — set EMAIL_BACKEND=smtp to switch from console logging
    email_backend: str = "console"       # "console" | "smtp"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from_address: str = "noreply@nyubites.com"
    email_from_name: str = "NYU Bites"

    # Frontend base URL for verification / reset links
    frontend_url: str = "http://localhost:3000"

    # AI — Groq (default) or OpenAI
    groq_api_key: str = ""
    openai_api_key: str = ""  # fallback if groq_api_key is empty

    # Google Places
    google_places_api_key: str = ""

    # App
    environment: str = "development"
    allowed_origins: str = "http://localhost:3000"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def async_database_url(self) -> str:
        """Ensures the URL uses the asyncpg driver, regardless of how it was provided."""
        url = self.database_url
        if url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()
