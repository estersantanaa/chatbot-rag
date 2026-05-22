import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

from ..config import settings
from .embeddings_provider import get_embeddings
from .retrieval_service import RetrievalService

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".txt", ".pdf"}


class IngestionService:
    def __init__(self):
        self.documents_path = settings.DOCUMENTS_PATH
        self.vector_db_path = settings.VECTOR_DB_PATH
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

    def _normalize_filename(self, filename: str) -> str:
        name = Path(filename).name
        if not name:
            raise ValueError("Nome de arquivo inválido.")
        suffix = Path(name).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Formato '{suffix}' não suportado. Envie apenas .txt ou .pdf."
            )
        return name

    def save_upload(self, filename: str, content: bytes) -> str:
        """Salva um arquivo enviado em DOCUMENTS_PATH."""
        safe_name = self._normalize_filename(filename)
        os.makedirs(self.documents_path, exist_ok=True)
        dest = os.path.join(self.documents_path, safe_name)
        with open(dest, "wb") as f:
            f.write(content)
        logger.info("Arquivo salvo em: %s", dest)
        return safe_name

    def load_file(self, file_path: str) -> List:
        """Carrega um único arquivo PDF ou TXT."""
        suffix = Path(file_path).suffix.lower()
        if suffix == ".txt":
            loader = TextLoader(file_path, encoding="utf-8")
            return loader.load()
        if suffix == ".pdf":
            loader = PyPDFLoader(file_path)
            return loader.load()
        return []

    def load_documents(self) -> List:
        """Varre a pasta de documentos e carrega arquivos PDF e TXT."""
        documents = []
        if not os.path.exists(self.documents_path):
            logger.warning(
                "Diretório de documentos não encontrado em: %s", self.documents_path
            )
            return documents

        for file in os.listdir(self.documents_path):
            file_path = os.path.join(self.documents_path, file)
            if not os.path.isfile(file_path):
                continue

            try:
                if Path(file).suffix.lower() in ALLOWED_EXTENSIONS:
                    logger.info("Carregando arquivo: %s", file)
                    documents.extend(self.load_file(file_path))
                else:
                    logger.debug("Ignorando arquivo não suportado: %s", file)
            except Exception as e:
                logger.error("Erro ao carregar o arquivo %s: %s", file, e)

        return documents

    def _build_index(self, docs: List) -> Dict[str, Any]:
        chunks = self.text_splitter.split_documents(docs)
        logger.info("Documentos divididos em %s blocos.", len(chunks))

        os.makedirs(self.vector_db_path, exist_ok=True)
        vector_db = FAISS.from_documents(chunks, get_embeddings())
        vector_db.save_local(self.vector_db_path)
        logger.info("Índice FAISS salvo em: %s", self.vector_db_path)

        RetrievalService.clear_cache()

        return {
            "success": True,
            "message": "Ingestão concluída com sucesso.",
            "documents_loaded": len(docs),
            "chunks_created": len(chunks),
            "vector_db_path": self.vector_db_path,
        }

    def run(self) -> Dict[str, Any]:
        """Reindexa todos os documentos em DOCUMENTS_PATH."""
        logger.info("Iniciando processo de ingestão de documentos...")

        docs = self.load_documents()
        if not docs:
            return {
                "success": False,
                "message": "Nenhum documento .txt ou .pdf encontrado para ingestão.",
                "documents_loaded": 0,
                "chunks_created": 0,
                "vector_db_path": self.vector_db_path,
            }

        logger.info("Total de %s páginas/documentos originais carregados.", len(docs))

        try:
            result = self._build_index(docs)
            result.setdefault("files_saved", [])
            result.setdefault("files_skipped", [])
            return result
        except Exception as e:
            logger.error("Erro ao criar/salvar banco vetorial FAISS: %s", e)
            return {
                "success": False,
                "message": f"Erro ao gerar índice vetorial: {e}",
                "documents_loaded": len(docs),
                "chunks_created": 0,
                "vector_db_path": self.vector_db_path,
                "files_saved": [],
                "files_skipped": [],
            }

    def ingest_uploads(self, files: List[Tuple[str, bytes]]) -> Dict[str, Any]:
        """
        Salva arquivos enviados e reindexa toda a pasta DOCUMENTS_PATH.
        files: lista de (nome_original, conteúdo_bytes).
        """
        files_saved: List[str] = []
        files_skipped: List[Dict[str, str]] = []

        for filename, content in files:
            if not content:
                files_skipped.append(
                    {"filename": filename or "desconhecido", "error": "Arquivo vazio."}
                )
                continue
            try:
                saved_name = self.save_upload(filename, content)
                files_saved.append(saved_name)
            except ValueError as e:
                files_skipped.append(
                    {"filename": filename or "desconhecido", "error": str(e)}
                )

        if not files_saved:
            return {
                "success": False,
                "message": "Nenhum arquivo válido foi salvo.",
                "files_saved": [],
                "files_skipped": files_skipped,
                "documents_loaded": 0,
                "chunks_created": 0,
                "vector_db_path": self.vector_db_path,
            }

        result = self.run()
        result["files_saved"] = files_saved
        result["files_skipped"] = files_skipped
        return result


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    service = IngestionService()
    outcome = service.run()
    print(outcome)
