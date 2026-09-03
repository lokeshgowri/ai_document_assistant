from pathlib import Path

import faiss
from fastapi import FastAPI, HTTPException

from app.models.schemas import AskRequest, AskResponse
from app.services.embeddings import EmbeddingService
from app.services.indexing_service import IndexingService
from app.services.rag_service import RAGService
from app.services.vector_store import VectorStore


app = FastAPI(
    title="AI Document Q&A Assistant",
    description=(
        "A Retrieval-Augmented Generation (RAG) API "
        "for answering questions from indexed documents "
        "using semantic search, keyword search, reranking, "
        "and a grounded language model."
    ),
    version="1.0.0"
)


embedding_service = EmbeddingService()
indexing_service = IndexingService()
rag_service = None


index_path = Path("data/index.faiss")
metadata_path = Path("data/metadata.json")


if index_path.exists() and metadata_path.exists():

    try:
        saved_index = faiss.read_index(
            str(index_path)
        )

        dimension = saved_index.d

        vector_store = VectorStore(dimension)

        vector_store.load(
            str(index_path)
        )

        rag_service = RAGService(
            vector_store=vector_store,
            embedding_service=embedding_service
        )

    except Exception:
        rag_service = None


@app.get(
    "/",
    tags=["System"],
    summary="Check API availability"
)
def root():

    return {
        "message": "AI Document Q&A Assistant is running."
    }


@app.get(
    "/health",
    tags=["System"],
    summary="Check application health"
)
def health_check():

    return {
        "status": "ok"
    }


@app.post(
    "/ask",
    response_model=AskResponse,
    tags=["Question Answering"],
    summary="Ask a question about the documents"
)
def ask_question(request: AskRequest):

    if rag_service is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Documents have not been indexed yet. "
                "Please call /index first."
            )
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

    except RuntimeError:

        raise HTTPException(
            status_code=500,
            detail="Failed to process the question."
        )


@app.post(
    "/index",
    tags=["Documents"],
    summary="Index documents"
)
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

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Failed to index documents."
        )