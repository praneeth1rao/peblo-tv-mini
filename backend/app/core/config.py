from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://peblo:peblo@localhost:5432/peblo"
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24
    STORAGE_BACKEND: str = "local"
    STORAGE_PATH: str = "./storage"
    CATALOGUE_DIR: str = "./storage/catalogue"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
