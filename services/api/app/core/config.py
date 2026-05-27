from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Neuromarket API"

    database_url: str = "postgresql+psycopg://neuromarket:neuromarket@localhost:5432/neuromarket"

    # Auth
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24
    google_client_id: str = ""

    # Filled in later phases.
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    deepseek_timeout_s: float = 60.0

    supabase_url: str = ""
    supabase_anon_key: str = ""


settings = Settings()
