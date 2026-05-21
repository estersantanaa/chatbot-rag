import os
import logging
from typing import List, Dict, Optional

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from ..config import settings

logger = logging.getLogger(__name__)


class RetrievalService:
    """Busca trechos relevantes no banco vetorial FAISS."""

    _vector_db: Optional[FAISS] = None
    _embeddings: Optional[HuggingFaceEmbeddings] = None

    def __init__(self):
        self.vector_db_path = settings.VECTOR_DB_PATH
        self.top_k = settings.RAG_TOP_K

    def _get_embeddings(self) -> HuggingFaceEmbeddings:
        if RetrievalService._embeddings is None:
            RetrievalService._embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"},
            )
        return RetrievalService._embeddings

    def _load_vector_db(self) -> Optional[FAISS]:
        if RetrievalService._vector_db is not None:
            return RetrievalService._vector_db

        index_path = os.path.join(self.vector_db_path, "index.faiss")
        if not os.path.exists(index_path):
            logger.warning(
                "Banco vetorial não encontrado em %s. Execute a ingestão primeiro.",
                self.vector_db_path,
            )
            return None

        try:
            RetrievalService._vector_db = FAISS.load_local(
                self.vector_db_path,
                self._get_embeddings(),
                allow_dangerous_deserialization=True,
            )
            return RetrievalService._vector_db
        except Exception as e:
            logger.error("Erro ao carregar FAISS: %s", e)
            return None

    def retrieve(self, query: str) -> List[Dict[str, str]]:
        """Retorna trechos semânticos relacionados à pergunta."""
        db = self._load_vector_db()
        if db is None:
            return []

        docs = db.similarity_search(query, k=self.top_k)
        results = []
        for doc in docs:
            source = os.path.basename(doc.metadata.get("source", "desconhecido"))
            results.append(
                {
                    "source": source,
                    "content": doc.page_content.strip(),
                }
            )
        return results
