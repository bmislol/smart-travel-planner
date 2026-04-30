import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, Field

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(BACKEND_DIR, ".env")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH, 
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # App Info
    PROJECT_NAME: str = "Smart Travel Planner"
    
    # Database (validates as a proper URL)
    DATABASE_URL: str 

    # Security (JWT)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API Keys
    ANTHROPIC_API_KEY: str
    WEATHER_API_KEY: str
    
    # Model Routing (Defaults to the 2026 versions)
    STRONG_MODEL: str = "claude-3-5-sonnet-latest"
    CHEAP_MODEL: str = "claude-3-haiku-20240307"
    
    # ML & RAG (Hardware: RTX 3060)
    EMBEDDING_MODEL_NAME: str = "all-mpnet-base-v2"
    CLASSIFIER_MODEL_PATH: str = "../data/models/winner_model.joblib"

# Singleton instance used across the app
settings = Settings()