from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GROQ_API_KEY: str
    DATABASE_URL: str = "sqlite:///./chatbot.db"
    VECTOR_DB_PATH: str = "vector_db"
    DOCUMENTS_PATH: str = "data"
    RAG_TOP_K: int = 4
    CHAT_HISTORY_LIMIT: int = 10
    DEBUG: bool = True

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
