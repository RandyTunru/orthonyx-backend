from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MAX_CONCURRENCY: int = 5
    OPENAI_TIMEOUT_SEC: int = 30

    model_config = {
        "env_file": ".env.app",
        "extra": "allow"
    }

openai_settings = Settings()