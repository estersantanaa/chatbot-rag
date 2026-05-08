import asyncio
from src.database import SessionLocal, engine, Base
from src.models.chat import ChatSession
from src.services.chat_service import ChatService

async def test_ai_core():
    print("--- Testando Núcleo de IA (Fase 3) ---")
    
    # 1. Garante que as tabelas existem
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 2. Cria uma nova sessão para este teste
        nova_sessao = ChatSession()
        db.add(nova_sessao)
        db.commit()
        db.refresh(nova_sessao)
        print(f"Sessão de teste criada: ID {nova_sessao.id}")
        
        chat = ChatService(db)
        
        # 3. Primeira interação
        print("\nUsuário: Olá, meu nome é Ester.")
        resposta1 = await chat.send_message(nova_sessao.id, "Olá, meu nome é Ester.")
        print(f"IA: {resposta1}")
        
        # 4. Segunda interação (Testando Memória)
        print("\nUsuário: Qual é o meu nome?")
        resposta2 = await chat.send_message(nova_sessao.id, "Qual é o meu nome?")
        print(f"IA: {resposta2}")
        
        if "Ester" in resposta2:
            print("\nSUCESSO: A IA lembrou do seu nome!")
        else:
            print("\nAVISO: A IA pode não ter captado o nome, verifique o contexto.")
            
    except Exception as e:
        print(f"\nERRO NO TESTE: {e}")
    finally:
        db.close()
        print("\n--- Fim do Teste ---")

if __name__ == "__main__":
    asyncio.run(test_ai_core())
