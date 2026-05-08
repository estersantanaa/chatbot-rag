from sqlalchemy.orm import Session
from ..models.chat import ChatSession, ChatMessage
from .ai_service import AIService

class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.ai = AIService()

    async def send_message(self, session_id: int, content: str):
        """
        Orquestra o envio de uma mensagem: salva no banco, busca histórico, chama IA, salva resposta.
        """
        # 1. Busca a sessão (ou cria uma se não existir, mas aqui assumimos que existe)
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise Exception(f"Sessão {session_id} não encontrada.")

        # 2. Salva a mensagem do usuário no banco
        user_msg = ChatMessage(
            session_id=session_id,
            role="user",
            content=content
        )
        self.db.add(user_msg)
        self.db.commit()

        # 3. Busca o histórico da sessão (últimas 10 mensagens para contexto)
        history = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.timestamp.asc())
            .all()
        )
        
        # Formatamos para o AIService (removendo a última que acabamos de adicionar para não duplicar)
        formatted_history = [
            {"role": msg.role, "content": msg.content} 
            for msg in history[:-1]
        ]

        # 4. Obtém resposta da IA
        ai_response_text = await self.ai.get_response(formatted_history, content)

        # 5. Salva a resposta da IA no banco
        ai_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=ai_response_text
        )
        self.db.add(ai_msg)
        self.db.commit()

        return ai_response_text
