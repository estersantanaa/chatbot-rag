from typing import List, Dict, Optional

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from ..config import settings

BASE_SYSTEM_PROMPT = """Você é o assistente virtual da ClownorCloud, provedor de nuvem com temática de circo.

Regras:
- Para perguntas sobre serviços, planos, preços ou FAQ da ClownorCloud, use APENAS as informações do CONTEXTO abaixo.
- Se o contexto não contiver a resposta, diga claramente que não encontrou essa informação na documentação.
- Para cumprimentos ou conversa casual, responda de forma breve e amigável, sem inventar dados da empresa.
- Responda em português do Brasil."""


class AIService:
    def __init__(self):
        self.model = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name="llama-3.3-70b-versatile",
            temperature=0.7,
        )

    def _build_system_prompt(self, context_chunks: List[Dict[str, str]]) -> str:
        if not context_chunks:
            return (
                BASE_SYSTEM_PROMPT
                + "\n\n(Nenhum trecho foi recuperado da base de conhecimento. "
                "Avise o usuário se a pergunta for sobre a empresa e sugira rodar a ingestão de documentos.)"
            )

        context_text = "\n\n---\n\n".join(
            f"[Fonte: {chunk['source']}]\n{chunk['content']}" for chunk in context_chunks
        )
        return f"{BASE_SYSTEM_PROMPT}\n\n### CONTEXTO RECUPERADO:\n{context_text}"

    async def get_response(
        self,
        messages_history: list,
        user_query: str,
        context_chunks: Optional[List[Dict[str, str]]] = None,
    ):
        """
        Gera uma resposta da IA baseada no histórico, contexto RAG e na nova pergunta.
        messages_history: Lista de dicionários {'role': '...', 'content': '...'}
        """
        system_prompt = self._build_system_prompt(context_chunks or [])
        formatted_messages = [SystemMessage(content=system_prompt)]

        for msg in messages_history:
            if msg["role"] == "user":
                formatted_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                formatted_messages.append(AIMessage(content=msg["content"]))

        formatted_messages.append(HumanMessage(content=user_query))

        response = await self.model.ainvoke(formatted_messages)
        return response.content
