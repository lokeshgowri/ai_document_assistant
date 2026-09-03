from fastapi import FastAPI, HTTPException
from pathlib import Path
import faiss

from app.models.schemas import AskRequest, AskResponse
from app.services.embeddings import EmbeddingService
from app.services.rag_service import RAGService
from app.services.vector_store import VectorStore
from app.services.indexing_service import IndexingService


app = FastAPI(
    title="AI Document Q&A Assistant",
    description="A RAG-based API for answering questions from documents.",
    version="1.0.0"
)


# --------------------------------------------------
# Create embedding service
# --------------------------------------------------

embedding_service = EmbeddingService()

indexing_service = IndexingService()

rag_service = None


# Check whether a saved index already exists
index_path = Path("data/index.faiss")
metadata_path = Path("data/metadata.json")

if index_path.exists() and metadata_path.exists():

    try:
        # Load saved FAISS index
        

        # Read the saved FAISS index
        saved_index = faiss.read_index(
            str(index_path)
            )
        # Get the actual dimension
        dimension = saved_index.d
        # Create VectorStore with the correct dimension
        vector_store = VectorStore(dimension)
        # Load the saved index + metadata
        vector_store.load(
            str(index_path)
        )

        # Create RAG service using loaded index
        rag_service = RAGService(
            vector_store=vector_store,
            embedding_service=embedding_service
        )

        print(
            "Existing FAISS index loaded successfully."
        )

    except Exception as exc:

        print(
            f"Failed to load existing index: {exc}"
        )


# --------------------------------------------------
# Root endpoint
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "AI Document Q&A Assistant is running."
    }


# --------------------------------------------------
# Health endpoint
# --------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }



# Ask endpoint


@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):

    if rag_service is None:
        raise HTTPException(
            status_code=400,
            detail="Documents have not been indexed yet. Please call /index first."
        )

    try:
        return rag_service.ask(
            question=request.question,
            top_k=request.top_k,
            source=request.source,
            section=request.section
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )
#indexing endpoint

@app.post("/index")
def index_documents():

    global rag_service

    try:
        result = indexing_service.build_index()

        rag_service = RAGService(
            vector_store=indexing_service.vector_store,
            embedding_service=indexing_service.embedding_service
        )

        return {
            "status": "success",
            "message": "Documents indexed successfully.",
            "details": result
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to index documents: {str(exc)}"
        )