from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    FERNET_KEY: str 
    API_KEY_EXPIRE_DAYS: int = 3

    class Config:
        env_file = ".env.app"

db_settings = Settings()