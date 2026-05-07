from sqlalchemy import create_engine
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
