from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# 1. O Engine (Motor): Conecta no arquivo SQLite
engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False} # Necessário para o SQLite funcionar com FastAPI
)

# 2. SessionLocal: A fábrica de sessões (conversas com o banco)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Base: A classe "mãe" que todas as nossas tabelas vão herdar
Base = declarative_base()

# 4. Função auxiliar para abrir/fechar o banco automaticamente
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema():
    """Cria tabelas e adiciona colunas novas em bancos SQLite já existentes."""
    from .models.chat import ChatMessage, ChatSession  # noqa: F401

    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    if "chat_sessions" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("chat_sessions")}
    with engine.begin() as conn:
        if "persona" not in columns:
            conn.execute(
                text(
                    "ALTER TABLE chat_sessions ADD COLUMN persona VARCHAR DEFAULT 'cloud'"
                )
            )
        conn.execute(
            text(
                "UPDATE chat_sessions SET persona = 'cloud' "
                "WHERE persona IS NULL OR persona = ''"
            )
        )
