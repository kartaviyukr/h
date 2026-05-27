from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Neuromarket API"

    # Filled in later phases; declared here as the single source of config.
    database_url: str = "postgresql://neuromarket:neuromarket@localhost:5432/neuromarket"
    deepseek_api_key: str = ""
    supabase_url: str = ""
    supabase_anon_key: str = ""


settings = Settings()
