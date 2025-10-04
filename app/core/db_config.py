from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    FERNET_KEY: str 
    API_KEY_EXPIRE_DAYS: int = 3

    REDIS_HOST: str 
    REDIS_PORT: int

    model_config = {
        "env_file": ".env.app",
        "extra": "allow"
    }

db_settings = Settings()