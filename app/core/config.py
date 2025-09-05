from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
    firebase_api_key: str = os.getenv("FIREBASE_API_KEY", "")
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")

def get_settings() -> Settings:
    return Settings()
