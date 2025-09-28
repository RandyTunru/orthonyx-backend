from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    FERNET_KEY: str 

    class Config:
        env_file = ".env.app"

settings = Settings()