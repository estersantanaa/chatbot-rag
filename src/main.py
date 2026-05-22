from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from .database import get_db, engine, Base
from .models.chat import ChatSession, ChatMessage
from .services.chat_service import ChatService
from .services.ingestion import IngestionService
from .services.embeddings_provider import EmbeddingLoadError

# Garante que as tabelas existem ao iniciar
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ClownorCloud AI API")

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

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API do ClownorCloud!", "status": "online"}

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
