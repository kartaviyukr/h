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

    # RAG (рецепты)
    rag_enabled: bool = True
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dim: int = 384
    rag_top_k: int = 5

    # Pricing (Phase 5)
    price_catalog_path: str = "data/price_catalog.json"
    price_providers: str = ""  # comma-separated provider codes; empty = all from catalog

    supabase_url: str = ""
    supabase_anon_key: str = ""


settings = Settings()
