import os
from src.config import settings
from src.services.ingestion import IngestionService
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

def test_ingestion_pipeline():
    print("=== INICIANDO TESTE DO PIPELINE DE INGESTÃO ===")
    
    # 1. Instancia e roda o serviço de Ingestão
    ingestion = IngestionService()
    result = ingestion.run()
    
    if not result.get("success"):
        print("\n[ERRO] O processo de ingestão falhou. Veja os logs acima.")
        return
        
    print("\n[SUCESSO] Ingestão concluída! Validando banco de dados vetorial...")
    
    # 2. Verifica se a pasta e os arquivos foram criados
    index_path = os.path.join(settings.VECTOR_DB_PATH, "index.faiss")
    pkl_path = os.path.join(settings.VECTOR_DB_PATH, "index.pkl")
    
    if not os.path.exists(index_path) or not os.path.exists(pkl_path):
        print(f"[ERRO] Os arquivos do FAISS não foram encontrados em: {settings.VECTOR_DB_PATH}")
        return
        
    print(f"Arquivos do FAISS verificados na pasta: '{settings.VECTOR_DB_PATH}'")
    
    # 3. Carrega o banco de dados criado para testar busca semântica
    print("\nCarregando banco de dados vetorial FAISS localmente...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    db = FAISS.load_local(
        settings.VECTOR_DB_PATH, 
        embeddings, 
        allow_dangerous_deserialization=True # Necessário para carregar arquivos pkl locais do FAISS
    )
    
    # 4. Faz uma consulta de teste
    test_queries = [
        "Qual é o preço do plano Grande Circo?",
        "Como funciona o suporte técnico corporativo?",
        "O que é o Clown-as-a-Service?"
    ]
    
    print("\n--- Realizando buscas semânticas de teste ---")
    for query in test_queries:
        print(f"\nPergunta: '{query}'")
        # Busca os 2 trechos mais similares
        results = db.similarity_search(query, k=2)
        
        print(f"Trechos recuperados ({len(results)}):")
        for i, doc in enumerate(results):
            source = os.path.basename(doc.metadata.get('source', 'desconhecido'))
            print(f"  [{i+1}] Fonte: {source}")
            # Mostra apenas as primeiras linhas para não inundar o terminal
            content_preview = doc.page_content.strip().replace('\n', ' | ')[:150]
            print(f"      Conteúdo: {content_preview}...")

    print("\n=== FIM DO TESTE DE INGESTÃO ===")

if __name__ == "__main__":
    test_ingestion_pipeline()
