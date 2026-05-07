from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

# Tabela de Sessões (Agrupa as mensagens de uma mesma conversa)
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Isso diz ao SQLAlchemy: "Uma sessão tem várias mensagens"
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

# Tabela de Mensagens (Cada fala do usuário ou do bot)
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id")) # ID da sessão "pai"
    role = Column(String)  # Quem falou: 'user' (você) ou 'assistant' (bot)
    content = Column(Text) # O texto da mensagem em si
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Isso diz ao SQLAlchemy: "Essa mensagem pertence a uma sessão específica"
    session = relationship("ChatSession", back_populates="messages")
