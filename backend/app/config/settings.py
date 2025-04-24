from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """
    Application settings utilizing Pydantic v2 for validation and environment loading.
    All environment variables will be automatically loaded from .env file.
    """
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Product Launch Planner"
    DEBUG: bool = False
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "AI-powered product launch planning and market analysis tool"
    
    # Security Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    CORS_ORIGINS: List[str] = ["http://161.97.151.50:3000"]
    
    # PostgreSQL Database (for user auth, plans, admin panel)
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "planner")
    POSTGRES_PORT: str = "5432"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    # MongoDB (for scraped data, prompts, logs, recipes)
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB: str = os.getenv("MONGODB_DB", "planner")
    
    # Email Settings
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    EMAIL_VERIFICATION_ENABLED: bool = False  # Set to False to disable email verification
    
    # AI/ML Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MODEL_NAME: str = "gemini-pro"
    DEFAULT_LLM_MODEL: str = "gemini-pro"
    MASTER_RECIPE_PROMPT_ID: str = "master-recipe-generator"
    MIN_PRODUCTS_FOR_MASTER_RECIPE: int = 1
    
    # Quotas and Limits
    DEFAULT_SCRAPE_QUOTA: int = 10
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD_SECONDS: int = 60
    
    # Training Settings
    TRAINING_ENABLED: bool = False
    MINIMUM_SAMPLES_FOR_TRAINING: int = 100
    
    # Analysis Settings
    MAX_CONCURRENT_ANALYSES: int = 5
    ANALYSIS_TIMEOUT_SECONDS: int = 300
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        if not self.SQLALCHEMY_DATABASE_URI and self.POSTGRES_SERVER:
            self.SQLALCHEMY_DATABASE_URI = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )


# Create settings object to be imported throughout the application
settings = Settings() 