from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/notesdb"
    JWT_SECRET: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    VERSION_HISTORY_LIMIT: int = 10

    class Config:
        env_file = ".env"


settings = Settings()
