import logging
from typing import Optional

from langchain_huggingface import HuggingFaceEmbeddings
from requests.exceptions import SSLError

from ..config import settings

logger = logging.getLogger(__name__)

_instance: Optional[HuggingFaceEmbeddings] = None


class EmbeddingLoadError(Exception):
    """Erro ao carregar o modelo de embeddings."""


def get_embeddings() -> HuggingFaceEmbeddings:
    global _instance
    if _instance is not None:
        return _instance

    model_name = (
        settings.EMBEDDING_MODEL_PATH
        if settings.EMBEDDING_MODEL_PATH
        else settings.EMBEDDING_MODEL
    )
    model_kwargs: dict = {"device": "cpu"}
    if settings.EMBEDDING_LOCAL_ONLY:
        model_kwargs["local_files_only"] = True

    try:
        logger.info("Carregando modelo de embeddings: %s", model_name)
        _instance = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
        )
        return _instance
    except SSLError as e:
        raise EmbeddingLoadError(
            "Falha SSL ao baixar o modelo do Hugging Face. "
            "Instale certifi (`pip install certifi`), reinicie o servidor, "
            "ou defina EMBEDDING_MODEL_PATH com o modelo baixado localmente. "
            f"Detalhe: {e}"
        ) from e
    except Exception as e:
        raise EmbeddingLoadError(
            f"Não foi possível carregar o modelo de embeddings ({model_name}): {e}"
        ) from e


def clear_embeddings_cache() -> None:
    global _instance
    _instance = None
