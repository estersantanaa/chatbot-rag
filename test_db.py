from src.database import engine, SessionLocal, Base
from src.models import ChatSession, ChatMessage

def test_database():
    print("--- Testando Camada de Dados ---")
    
    # 1. Cria as tabelas no arquivo .db
    print("Criando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    
    # 2. Abre uma sessão com o banco
    db = SessionLocal()
    
    try:
        # 3. Cria uma nova sessão de chat
        print("Criando uma nova sessao de chat...")
        nova_sessao = ChatSession()
        db.add(nova_sessao)
        db.commit() # Salva no banco
        db.refresh(nova_sessao) # Pega o ID gerado
        
        print(f"Sessao criada com ID: {nova_sessao.id}")
        
        # 4. Cria uma mensagem de teste
        print("Salvando uma mensagem de teste...")
        nova_msg = ChatMessage(
            session_id=nova_sessao.id,
            role="user",
            content="Segunda mensagem de teste, agora com persistencia!"
        )
        db.add(nova_msg)
        db.commit()
        
        # 5. Verifica se salvou mesmo
        sessao_do_banco = db.query(ChatSession).filter(ChatSession.id == nova_sessao.id).first()
        print(f"Sucesso! Mensagens na sessao: {len(sessao_do_banco.messages)}")
        print(f"Conteudo da mensagem: {sessao_do_banco.messages[0].content}")
        
    except Exception as e:
        print(f"Erro no teste do banco: {e}")
    finally:
        db.close()
        print("-------------------------------")

if __name__ == "__main__":
    test_database()
