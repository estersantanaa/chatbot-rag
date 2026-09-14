from typing import List, Dict, Optional

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from ..config import settings

BASE_SYSTEM_PROMPT = """Você é o assistente virtual da ClownorCloud, um chatbot RAG de documentação.

Regras:
- Para perguntas sobre o projeto, a stack, a ingestão ou pessoas citadas na base (incluindo Ester Santana), use APENAS o CONTEXTO abaixo.
- Se o contexto tiver a resposta, use-a. Só diga que não encontrou se o CONTEXTO realmente não trouxer o fato.
- Para cumprimentos ou conversa casual, responda de forma breve e amigável, sem inventar dados da empresa.
- Responda em português do Brasil.
- Formate a resposta em Markdown quando ajudar a leitura: negrito, listas, títulos curtos e código inline se fizer sentido. Não use HTML."""

PERSONA_PROMPTS = {
    "cloud": (
        "Persona Cloud: secretário corporativo. Seja educado, formal e objetivo, "
        "como quem organiza a agenda de um escritório. Linguagem polida, sem gíria, "
        "sem emoji, sem piada. Cumprimente com cortesia quando fizer sentido."
    ),
    "clown": (
        "Persona Clown: responda de forma engraçada e leve, sempre respeitosa "
        "(nada de ofensa, deboche pesado ou constrangimento). Use emojis com naturalidade. "
        "O humor não pode inventar fatos fora do contexto."
    ),
}


class AIService:
    def __init__(self):
        self.model = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL,
            temperature=0.2,
        )

    def _build_system_prompt(
        self,
        context_chunks: List[Dict[str, str]],
        persona: str = "cloud",
    ) -> str:
        persona_line = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS["cloud"])
        prompt = f"{BASE_SYSTEM_PROMPT}\n- {persona_line}"

        if not context_chunks:
            return (
                prompt
                + "\n\n(Nenhum trecho foi recuperado da base de conhecimento. "
                "Avise o usuário se a pergunta for sobre a empresa e sugira enviar um documento.)"
            )

        context_text = "\n\n---\n\n".join(
            f"[Fonte: {chunk['source']}]\n{chunk['content']}" for chunk in context_chunks
        )
        return f"{prompt}\n\n### CONTEXTO RECUPERADO:\n{context_text}"

    async def get_response(
        self,
        messages_history: list,
        user_query: str,
        context_chunks: Optional[List[Dict[str, str]]] = None,
        persona: str = "cloud",
    ):
        """
        Gera uma resposta da IA baseada no histórico, contexto RAG e na nova pergunta.
        messages_history: Lista de dicionários {'role': '...', 'content': '...'}
        """
        system_prompt = self._build_system_prompt(context_chunks or [], persona=persona)
        formatted_messages = [SystemMessage(content=system_prompt)]

        for msg in messages_history:
            if msg["role"] == "user":
                formatted_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                formatted_messages.append(AIMessage(content=msg["content"]))

        formatted_messages.append(HumanMessage(content=user_query))

        response = await self.model.ainvoke(formatted_messages)
        return response.content
