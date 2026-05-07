import asyncio
from src.config import settings
from langchain_groq import ChatGroq

async def test_api():
    print("--- Iniciando Teste de Conexao ---")
    print(f"Chave encontrada: {'Sim' if settings.GROQ_API_KEY else 'Nao'}")
    
    try:
        model = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY, 
            model_name="llama-3.3-70b-versatile"
        )
        
        print("Enviando mensagem para o Groq...")
        response = await model.ainvoke("Diga apenas: 'Conexao com Groq estabelecida com sucesso!'")
        
        print("\nSUCESSO!")
        print(f"Resposta da IA: {response.content}")
        
    except Exception as e:
        print("\nERRO DE CONEXAO:")
        print(str(e))
    
    print("---------------------------------")

if __name__ == "__main__":
    asyncio.run(test_api())
