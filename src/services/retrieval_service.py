import os
import re
import logging
from typing import Any, List, Dict, Optional, Tuple

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from ..config import settings
from .embeddings_provider import get_embeddings

logger = logging.getLogger(__name__)

_STOPWORDS = {
    "quem",
    "qual",
    "quais",
    "como",
    "sobre",
    "para",
    "pelo",
    "pela",
    "uma",
    "uns",
    "umas",
    "esse",
    "essa",
    "este",
    "esta",
    "isto",
    "desse",
    "desta",
    "neste",
    "nesta",
    "chatbot",
    "projeto",
    "base",
    "quais",
    "que",
    "com",
    "dos",
    "das",
    "nos",
    "nas",
    "what",
    "who",
    "this",
    "that",
    "from",
    "with",
}


class RetrievalService:
    """Busca trechos relevantes no banco vetorial FAISS."""

    _vector_db: Optional[FAISS] = None
    _embeddings: Optional[HuggingFaceEmbeddings] = None

    def __init__(self):
        self.vector_db_path = settings.VECTOR_DB_PATH
        self.top_k = settings.RAG_TOP_K
        self.score_threshold = settings.RAG_SCORE_THRESHOLD

    def _get_embeddings(self) -> HuggingFaceEmbeddings:
        if RetrievalService._embeddings is None:
            RetrievalService._embeddings = get_embeddings()
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

    @classmethod
    def clear_cache(cls) -> None:
        """Invalida o índice em memória após reindexação."""
        cls._vector_db = None

    def _query_terms(self, query: str) -> List[str]:
        tokens = re.findall(r"[0-9a-zà-ÿ]+", query.lower())
        return [token for token in tokens if len(token) >= 4 and token not in _STOPWORDS]

    def _all_documents(self, db: FAISS) -> List:
        store = getattr(db.docstore, "_dict", {})
        return list(store.values())

    def _chunk_key(self, source: str, content: str) -> Tuple[str, str]:
        return (source, content[:180])

    def _to_result(self, doc, score: Optional[float]) -> Dict[str, Any]:
        source = os.path.basename(doc.metadata.get("source", "desconhecido"))
        return {
            "source": source,
            "content": doc.page_content.strip(),
            "score": score,
        }

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """Retorna trechos semânticos e léxicos relacionados à pergunta."""
        db = self._load_vector_db()
        if db is None:
            return []

        search_k = max(self.top_k, 8)
        docs_with_scores = db.similarity_search_with_score(query, k=search_k)

        ranked: List[Dict[str, Any]] = []
        seen = set()

        terms = self._query_terms(query)
        if terms:
            for doc in self._all_documents(db):
                source = os.path.basename(doc.metadata.get("source", "desconhecido"))
                blob = f"{doc.page_content} {source}".lower()
                if any(term in blob for term in terms):
                    key = self._chunk_key(source, doc.page_content.strip())
                    if key in seen:
                        continue
                    seen.add(key)
                    ranked.append(self._to_result(doc, score=None))

        for doc, score in docs_with_scores:
            score_value = float(score)
            if (
                self.score_threshold is not None
                and score_value > self.score_threshold
            ):
                continue
            source = os.path.basename(doc.metadata.get("source", "desconhecido"))
            content = doc.page_content.strip()
            key = self._chunk_key(source, content)
            if key in seen:
                continue
            seen.add(key)
            ranked.append(self._to_result(doc, score_value))

        return ranked[: max(self.top_k, 6)]
