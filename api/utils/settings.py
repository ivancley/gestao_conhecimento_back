from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file = ".env", env_file_encoding = "utf-8", extra="ignore"
    )
    
    DATABASE_URL: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str

    # SMTP
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FRONTEND_URL: str
    
    # Celery
    #CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    #CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    
settings = Settings()