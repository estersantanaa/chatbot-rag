from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from .config import settings
from .database import get_db, engine, Base
from .models.chat import ChatSession, ChatMessage
from .services.chat_service import ChatService
from .services.ingestion import ALLOWED_EXTENSIONS, IngestionService
from .services.embeddings_provider import EmbeddingLoadError, get_embeddings

# Garante que as tabelas existem ao iniciar
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI API")

# Configuração de CORS para permitir que o frontend acesse a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Modelos Pydantic (Validação de Dados) ---

class MessageRequest(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True

class SessionResponse(BaseModel):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SourceResponse(BaseModel):
    source: str
    excerpt: str
    score: Optional[float] = None

class ChatResponse(BaseModel):
    response: str
    sources: List[SourceResponse]

class SkippedFileResponse(BaseModel):
    filename: str
    error: str

class IngestResponse(BaseModel):
    success: bool
    message: str
    files_saved: List[str] = []
    files_skipped: List[SkippedFileResponse] = []
    documents_loaded: int = 0
    chunks_created: int = 0
    vector_db_path: str = ""

class DocumentResponse(BaseModel):
    filename: str
    extension: str
    size_bytes: int
    modified_at: datetime

class DeleteDocumentResponse(BaseModel):
    success: bool
    message: str
    deleted_filename: str
    remaining_documents_count: int
    reindex: IngestResponse

class RagHealthResponse(BaseModel):
    status: str
    documents_path: str
    documents_path_exists: bool
    supported_documents_count: int
    supported_documents: List[str]
    vector_db_path: str
    vector_index_exists: bool
    vector_metadata_exists: bool
    ready_for_retrieval: bool
    rag_top_k: int
    rag_score_threshold: Optional[float] = None
    embedding_model: str
    embeddings_checked: bool = False
    embeddings_ok: Optional[bool] = None
    embedding_error: Optional[str] = None

# --- Endpoints ---

def _get_documents_dir() -> Path:
    return Path(settings.DOCUMENTS_PATH)

def _resolve_document_path(filename: str) -> Path:
    safe_name = Path(filename).name
    if safe_name != filename or not safe_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de arquivo inválido.",
        )

    suffix = Path(safe_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Documento deve ser .txt ou .pdf.",
        )

    return _get_documents_dir() / safe_name

def _list_document_files() -> List[Path]:
    documents_path = _get_documents_dir()
    if not documents_path.exists():
        return []

    return sorted(
        (
            file
            for file in documents_path.iterdir()
            if file.is_file() and file.suffix.lower() in ALLOWED_EXTENSIONS
        ),
        key=lambda file: file.name.lower(),
    )

def _to_document_response(file: Path) -> DocumentResponse:
    stat = file.stat()
    return DocumentResponse(
        filename=file.name,
        extension=file.suffix.lower(),
        size_bytes=stat.st_size,
        modified_at=datetime.fromtimestamp(stat.st_mtime),
    )

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API do ClownorCloud!", "status": "online"}

@app.get("/health/rag", response_model=RagHealthResponse)
def rag_health(check_embeddings: bool = False):
    """
    Verifica se os arquivos necessários para o RAG existem.
    Use `check_embeddings=true` para também carregar o modelo de embeddings.
    """
    documents_path = Path(settings.DOCUMENTS_PATH)
    vector_db_path = Path(settings.VECTOR_DB_PATH)
    index_path = vector_db_path / "index.faiss"
    metadata_path = vector_db_path / "index.pkl"

    supported_documents = []
    if documents_path.exists():
        supported_documents = sorted(
            file.name
            for file in documents_path.iterdir()
            if file.is_file() and file.suffix.lower() in {".txt", ".pdf"}
        )

    embedding_model = (
        settings.EMBEDDING_MODEL_PATH
        if settings.EMBEDDING_MODEL_PATH
        else settings.EMBEDDING_MODEL
    )
    vector_index_exists = index_path.exists()
    vector_metadata_exists = metadata_path.exists()
    ready_for_retrieval = vector_index_exists and vector_metadata_exists

    embeddings_ok = None
    embedding_error = None
    if check_embeddings:
        try:
            get_embeddings()
            embeddings_ok = True
        except EmbeddingLoadError as e:
            embeddings_ok = False
            embedding_error = str(e)

    status_value = "healthy"
    if not ready_for_retrieval:
        status_value = "not_ready"
    if check_embeddings and embeddings_ok is False:
        status_value = "degraded"

    return RagHealthResponse(
        status=status_value,
        documents_path=str(documents_path),
        documents_path_exists=documents_path.exists(),
        supported_documents_count=len(supported_documents),
        supported_documents=supported_documents,
        vector_db_path=str(vector_db_path),
        vector_index_exists=vector_index_exists,
        vector_metadata_exists=vector_metadata_exists,
        ready_for_retrieval=ready_for_retrieval,
        rag_top_k=settings.RAG_TOP_K,
        rag_score_threshold=settings.RAG_SCORE_THRESHOLD,
        embedding_model=embedding_model,
        embeddings_checked=check_embeddings,
        embeddings_ok=embeddings_ok,
        embedding_error=embedding_error,
    )

@app.post("/ingest", response_model=IngestResponse)
async def ingest_documents(
    response: Response,
    files: List[UploadFile] = File(
        ...,
        description="Um ou mais arquivos .pdf ou .txt para salvar e reindexar",
    ),
):
    """
    Faz upload de documentos, salva em `data/` e reconstrói o índice FAISS
    com todos os arquivos da pasta.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Envie pelo menos um arquivo (.pdf ou .txt).",
        )

    uploads = []
    for upload in files:
        content = await upload.read()
        uploads.append((upload.filename or "documento", content))

    try:
        result = IngestionService().ingest_uploads(uploads)
    except EmbeddingLoadError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    response.status_code = (
        status.HTTP_201_CREATED
        if result["success"]
        else status.HTTP_422_UNPROCESSABLE_ENTITY
    )
    return IngestResponse(**result)

@app.post("/ingest/rebuild", response_model=IngestResponse)
def rebuild_index():
    """Reindexa todos os .pdf e .txt já presentes em `data/` sem upload."""
    try:
        result = IngestionService().run()
    except EmbeddingLoadError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result["message"],
        )
    return IngestResponse(**result)

@app.get("/documents", response_model=List[DocumentResponse])
def list_documents():
    """Lista documentos .pdf e .txt disponíveis para o RAG."""
    return [_to_document_response(file) for file in _list_document_files()]

@app.delete("/documents/{filename}", response_model=DeleteDocumentResponse)
def delete_document(filename: str):
    """Remove um documento de `data/` e reconstrói o índice FAISS."""
    document_path = _resolve_document_path(filename)
    if not document_path.exists() or not document_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento não encontrado.",
        )

    document_path.unlink()
    service = IngestionService()
    remaining_documents = _list_document_files()

    if remaining_documents:
        try:
            result = service.run()
        except EmbeddingLoadError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(e),
            ) from e
    else:
        service.clear_index()
        result = {
            "success": True,
            "message": "Documento removido. Nenhum documento restante; índice FAISS limpo.",
            "files_saved": [],
            "files_skipped": [],
            "documents_loaded": 0,
            "chunks_created": 0,
            "vector_db_path": settings.VECTOR_DB_PATH,
        }

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result["message"],
        )

    return DeleteDocumentResponse(
        success=True,
        message="Documento removido e índice atualizado.",
        deleted_filename=document_path.name,
        remaining_documents_count=len(remaining_documents),
        reindex=IngestResponse(**result),
    )

@app.post("/sessions", response_model=SessionResponse)
def create_session(db: Session = Depends(get_db)):
    """Cria uma nova sessão de chat."""
    new_session = ChatSession()
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@app.get("/sessions", response_model=List[SessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    """Lista todas as sessões existentes."""
    return db.query(ChatSession).order_by(ChatSession.created_at.desc()).all()

@app.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_message(session_id: int, request: MessageRequest, db: Session = Depends(get_db)):
    """Envia uma mensagem para a IA em uma sessão específica (com RAG)."""
    chat_service = ChatService(db)
    try:
        return await chat_service.send_message(session_id, request.content)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/sessions/{session_id}/history", response_model=List[MessageResponse])
def get_history(session_id: int, db: Session = Depends(get_db)):
    """Retorna o histórico de mensagens de uma sessão."""
    history = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp.asc()).all()
    if not history and not db.query(ChatSession).filter(ChatSession.id == session_id).first():
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    return history
