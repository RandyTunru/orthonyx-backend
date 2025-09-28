from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    # other env values if needed
    API_KEY_EXPIRE_DAYS: int = 3
    FERNET_KEY: str 

    class Config:
        env_file = ".env.app"

settings = Settings()