from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
print(f'env file : {_ENV_FILE}')

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/inventory_db"
    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = str(_ENV_FILE)
        env_file_encoding = "utf-8"

settings = Settings()
