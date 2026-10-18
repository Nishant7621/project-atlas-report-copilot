"""
FastAPI Server for Project Atlas.
Provides:
- POST /chat (structured enterprise response)
- POST /ingest (document ingestion & vector index refresh)
- GET /escalations (tickets for human analysts)
- GET /health (system health check & metrics)
- POST /feedback (user thumbs-up / thumbs-down ratings)
"""

import time
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Header, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import settings
from app.database.connection import init_db, SessionLocal
from app.database.models import Escalation, ChatFeedback
from app.rag.chunker import ReportChunker
from app.rag.vector_store import get_vector_store
from app.agent.workflow import AgentWorkflow

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("atlas_api")

app = FastAPI(
    title="Project Atlas: Enterprise Report Copilot API",
    version="1.0.0",
    description="Agentic RAG Copilot with Entitlement Control, Conflict Detection, and Guardrails."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
def startup_event():
    init_db()
    # Preload vector store
    get_vector_store()
    logger.info("Project Atlas FastAPI Service started successfully.")

# Authentication dependency
def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    # Allow local development bypass or verify against settings.API_KEY
    if settings.ENVIRONMENT == "development" and not x_api_key:
        return True
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header"
        )
    return True

# --- Pydantic Data Models ---

class ChatRequest(BaseModel):
    client_id: str = Field(..., example="C-01", description="Identifier of calling client")
    message: str = Field(..., example="What was the global smart water meter market size in 2024?", description="Question prompt")

class Citation(BaseModel):
    report_id: str
    page: int
    label: str
    snippet: Optional[str] = None

class Conflict(BaseModel):
    metric: str
    sources: List[Dict[str, Any]]
    explanation: str

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
    confidence: float
    conflicts: List[Conflict] = []
    derived_values: List[Dict[str, Any]] = []
    escalated: bool

class FeedbackRequest(BaseModel):
    client_id: str
    question: str
    answer: str
    rating: str = Field(..., example="up", description="'up' or 'down'")

class IngestResponse(BaseModel):
    status: str
    total_reports_processed: int
    total_chunks_indexed: int

# --- API Endpoints ---

@app.get("/health", tags=["Monitoring"])
def health_check():
    vector_store = get_vector_store()
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database_url": settings.DATABASE_URL.split("@")[-1],
        "indexed_chunks": len(vector_store.chunks),
        "total_documents": vector_store.total_docs
    }

@app.post("/chat", response_model=ChatResponse, tags=["Agent"])
def chat_endpoint(payload: ChatRequest, authorized: bool = Depends(verify_api_key)):
    start_time = time.time()
    workflow = AgentWorkflow()
    
    try:
        response_dict = workflow.process_query(
            client_id=payload.client_id,
            question=payload.message
        )
        latency = time.time() - start_time
        logger.info(f"Query completed in {latency:.2f}s for Client {payload.client_id}")
        return response_dict
    except Exception as e:
        logger.error(f"Error handling query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal agent error: {str(e)}")

@app.post("/ingest", response_model=IngestResponse, tags=["RAG"])
def ingest_documents(authorized: bool = Depends(verify_api_key)):
    chunker = ReportChunker(settings.REPORTS_DIR)
    chunks = chunker.chunk_all_reports()
    
    vector_store = get_vector_store()
    vector_store.build_index(chunks)
    
    reports_count = len(list(settings.REPORTS_DIR.glob("*.md")))
    return {
        "status": "success",
        "total_reports_processed": reports_count,
        "total_chunks_indexed": len(chunks)
    }

@app.get("/escalations", tags=["Escalations"])
def get_escalations(authorized: bool = Depends(verify_api_key)):
    from app.agent.escalation import EscalationManager
    return EscalationManager.get_all_escalations()

@app.post("/feedback", tags=["Feedback"])
def record_feedback(payload: FeedbackRequest):
    session = SessionLocal()
    try:
        fb = ChatFeedback(
            client_id=payload.client_id,
            question=payload.question,
            answer=payload.answer,
            rating=payload.rating
        )
        session.add(fb)
        session.commit()
        return {"status": "success", "message": "Feedback recorded"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()
