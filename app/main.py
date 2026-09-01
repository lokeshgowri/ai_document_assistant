from fastapi import FastAPI, HTTPException

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


# --------------------------------------------------
# Sample document chunks
# --------------------------------------------------

chunks = [
    {
        "source": "sample.txt",
        "text": "Employees are entitled to 20 days of annual leave per year."
    },
    {
        "source": "sample.txt",
        "text": "Employees should submit leave requests through the HR portal."
    },
    {
        "source": "sample.txt",
        "text": "Leave requests should be submitted at least three working days in advance."
    }
]


# --------------------------------------------------
# Create embeddings for sample chunks
# --------------------------------------------------

texts = [
    chunk["text"]
    for chunk in chunks
]

embeddings = embedding_service.embed_texts(texts)


# --------------------------------------------------
# Create FAISS vector store
# --------------------------------------------------

dimension = len(embeddings[0])

vector_store = VectorStore(dimension)

vector_store.add_vectors(
    embeddings,
    chunks
)


# --------------------------------------------------
# Create RAG service
# --------------------------------------------------

rag_service = None


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
            top_k=request.top_k
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