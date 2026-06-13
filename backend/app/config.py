from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List

# Resolve .env path relative to this file, not the launch directory.
# This ensures the .env file is always found regardless of where uvicorn is run.
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
print(f'env file : {_ENV_FILE}')

class Settings(BaseSettings):
    # These are fallback defaults only.
    # In production, set these as environment variables on Render/Railway/etc.
    # Locally, they are overridden by the .env file found at: backend/.env
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/inventory_db"
    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = str(_ENV_FILE)
        env_file_encoding = "utf-8"

settings = Settings()
