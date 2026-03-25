from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    supabase_url: str = ""
    supabase_key: str = ""
    frontend_url: str = "http://localhost:3000"
    port: int = 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()
