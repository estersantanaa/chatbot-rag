from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GROQ_API_KEY: str
    DATABASE_URL: str = "sqlite:///./chatbot.db"
    DEBUG: bool = True

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
