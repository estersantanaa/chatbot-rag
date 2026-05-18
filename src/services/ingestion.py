import os
import logging
from typing import List

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

from ..config import settings

# Configura o logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class IngestionService:
    def __init__(self):
        self.documents_path = settings.DOCUMENTS_PATH
        self.vector_db_path = settings.VECTOR_DB_PATH
        # Modelo leve e gratuito do HuggingFace executado localmente na máquina
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

    def load_documents(self) -> List:
        """Varre a pasta de documentos e carrega arquivos PDF e TXT."""
        documents = []
        if not os.path.exists(self.documents_path):
            logger.warning(f"Diretório de documentos não encontrado em: {self.documents_path}")
            return documents

        for file in os.listdir(self.documents_path):
            file_path = os.path.join(self.documents_path, file)
            if not os.path.isfile(file_path):
                continue

            try:
                if file.endswith(".txt"):
                    logger.info(f"Carregando arquivo de texto: {file}")
                    loader = TextLoader(file_path, encoding="utf-8")
                    documents.extend(loader.load())
                elif file.endswith(".pdf"):
                    logger.info(f"Carregando arquivo PDF: {file}")
                    loader = PyPDFLoader(file_path)
                    documents.extend(loader.load())
                else:
                    logger.debug(f"Ignorando arquivo não suportado: {file}")
            except Exception as e:
                logger.error(f"Erro ao carregar o arquivo {file}: {str(e)}")

        return documents

    def run(self) -> bool:
        """Orquestra o pipeline completo de ingestão."""
        logger.info("Iniciando processo de ingestão de documentos...")
        
        # 1. Carregar documentos
        docs = self.load_documents()
        if not docs:
            logger.warning("Nenhum documento encontrado na pasta data/ para ingestão.")
            return False

        logger.info(f"Total de {len(docs)} páginas/documentos originais carregados.")

        # 2. Dividir documentos em chunks
        logger.info("Dividindo documentos em blocos (chunks)...")
        chunks = self.text_splitter.split_documents(docs)
        logger.info(f"Documentos divididos em {len(chunks)} blocos.")

        # 3. Gerar Embeddings e Salvar no FAISS
        logger.info("Gerando embeddings e criando banco de dados vetorial FAISS...")
        try:
            # Cria a pasta vector_db se não existir
            os.makedirs(self.vector_db_path, exist_ok=True)
            
            # Cria a base do FAISS a partir dos chunks e embeddings
            vector_db = FAISS.from_documents(chunks, self.embeddings)
            
            # Salva localmente
            vector_db.save_local(self.vector_db_path)
            logger.info(f"Banco de dados vetorial FAISS salvo com sucesso em: {self.vector_db_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar/salvar banco vetorial FAISS: {str(e)}")
            return False

if __name__ == "__main__":
    # Permite rodar o arquivo diretamente como um script independente caso parent modules estejam no path
    service = IngestionService()
    service.run()
