from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.
    Create a .env file in the backend directory with your API keys.
    """

    youtube_api_key: str
    tmdb_api_key: str
    database_url: str = "sqlite+aiosqlite:///./quickflicks.db"
    api_timeout: int = 10
    cache_ttl: int = 180
    max_results_per_query: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()
