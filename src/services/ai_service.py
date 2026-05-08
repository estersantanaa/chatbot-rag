from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ..config import settings

class AIService:
    def __init__(self):
        self.model = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name="llama-3.3-70b-versatile",
            temperature=0.7
        )
        # O prompt de sistema será configurado pela usuária posteriormente
        self.system_prompt = "Você é um assistente prestativo."

    async def get_response(self, messages_history: list, user_query: str):
        """
        Gera uma resposta da IA baseada no histórico e na nova pergunta.
        messages_history: Lista de dicionários {'role': '...', 'content': '...'}
        """
        
        # 1. Prepara a lista de mensagens para o LangChain
        formatted_messages = [SystemMessage(content=self.system_prompt)]
        
        # 2. Adiciona o histórico
        for msg in messages_history:
            if msg['role'] == 'user':
                formatted_messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                formatted_messages.append(AIMessage(content=msg['content']))
        
        # 3. Adiciona a pergunta atual
        formatted_messages.append(HumanMessage(content=user_query))
        
        # 4. Chama a API
        response = await self.model.ainvoke(formatted_messages)
        
        return response.content
