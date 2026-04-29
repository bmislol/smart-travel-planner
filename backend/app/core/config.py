from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
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
    STRONG_MODEL: str = "claude-4-6-sonnet"
    CHEAP_MODEL: str = "claude-4-5-haiku"
    
    # ML & RAG (Hardware: RTX 3060)
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    CLASSIFIER_MODEL_PATH: str = "../data/models/winner_model.joblib"

# Singleton instance used across the app
settings = Settings()