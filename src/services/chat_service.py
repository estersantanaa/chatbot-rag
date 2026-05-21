from sqlalchemy.orm import Session

from ..config import settings
from ..models.chat import ChatSession, ChatMessage
from .ai_service import AIService
from .retrieval_service import RetrievalService


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.ai = AIService()
        self.retrieval = RetrievalService()

    async def send_message(self, session_id: int, content: str) -> dict:
        """
        Orquestra o envio de uma mensagem: salva, recupera contexto RAG, chama IA, salva resposta.
        """
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise Exception(f"Sessão {session_id} não encontrada.")

        user_msg = ChatMessage(
            session_id=session_id,
            role="user",
            content=content,
        )
        self.db.add(user_msg)
        self.db.commit()

        history = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.timestamp.asc())
            .all()
        )

        prior_messages = history[:-1][-settings.CHAT_HISTORY_LIMIT :]
        formatted_history = [
            {"role": msg.role, "content": msg.content} for msg in prior_messages
        ]

        context_chunks = self.retrieval.retrieve(content)

        ai_response_text = await self.ai.get_response(
            formatted_history, content, context_chunks=context_chunks
        )

        ai_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=ai_response_text,
        )
        self.db.add(ai_msg)
        self.db.commit()

        return {
            "response": ai_response_text,
            "sources": [
                {
                    "source": chunk["source"],
                    "excerpt": chunk["content"][:300],
                }
                for chunk in context_chunks
            ],
        }
