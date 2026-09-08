from pathlib import Path

import faiss
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.schemas import (
    AskRequest,
    AskResponse,
    ConversationCreate,
    ConversationResponse,
    ConversationDetailResponse
)
from app.services.conversation_service import ConversationService
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://lokeshgowri.github.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
def ask_question(
    request: AskRequest,
    db: Session = Depends(get_db)
):

    if rag_service is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Documents have not been indexed yet. "
                "Please call /index first."
            )
        )

    conversation_service = ConversationService(db)

    # ---------------------------------------------------------
    # 1. Validate conversation if conversation_id is provided
    # ---------------------------------------------------------

    if request.conversation_id is not None:

        conversation = conversation_service.get_conversation(
            request.conversation_id
        )

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found."
            )

        # Save user's question
        conversation_service.add_message(
            conversation_id=request.conversation_id,
            role="user",
            content=request.question
        )

    # ---------------------------------------------------------
    # 2. Run existing RAG pipeline
    # ---------------------------------------------------------

    try:

        response = rag_service.ask(
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

    # ---------------------------------------------------------
    # 3. Save assistant response
    # ---------------------------------------------------------

    if request.conversation_id is not None:

        conversation_service.add_message(
            conversation_id=request.conversation_id,
            role="assistant",
            content=response["answer"]
        )

    # ---------------------------------------------------------
    # 4. Return normal RAG response
    # ---------------------------------------------------------

    return response


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

    except Exception as exc:
        print(f"INDEX ERROR: {exc}")

        raise HTTPException(
            status_code=500,
            detail="Failed to index documents."
        )

@app.get(
    "/index/status",
    tags=["Documents"],
    summary="Get current index status"
)
def get_index_status():

    return indexing_service.get_index_status()


@app.post(
    "/upload",
    tags=["Documents"],
    summary="Upload a document"
)
async def upload_document(file: UploadFile = File(...)):

    allowed_extensions = {
        ".pdf",
        ".docx",
        ".txt"
    }

    filename = file.filename

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected."
        )

    # Get file extension
    extension = "." + filename.split(".")[-1].lower()

    # Validate extension
    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Only PDF, DOCX, and TXT files are allowed."
            )
        )

    try:

        # Create data directory if it doesn't exist
        data_directory = "data"

        import os

        os.makedirs(
            data_directory,
            exist_ok=True
        )

        # Create file path
        file_path = os.path.join(
            data_directory,
            filename
        )

        # Read uploaded file
        contents = await file.read()

        # Save file
        with open(file_path, "wb") as destination:

            destination.write(contents)

        return {
            "status": "success",
            "message": "Document uploaded successfully.",
            "filename": filename
        }

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Failed to upload document."
        )

@app.post(
    "/conversations",
    response_model=ConversationResponse,
    tags=["Conversations"],
    summary="Create a new conversation"
)
def create_conversation(
    request: ConversationCreate,
    db: Session = Depends(get_db)
):

    service = ConversationService(db)

    conversation = service.create_conversation(
        title=request.title
    )

    return conversation

@app.get(
    "/conversations",
    response_model=list[ConversationResponse],
    tags=["Conversations"],
    summary="Get all active conversations"
)
def get_conversations(
    db: Session = Depends(get_db)
):

    service = ConversationService(db)

    return service.get_conversations()

@app.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
    tags=["Conversations"],
    summary="Get a conversation with its messages"
)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):

    service = ConversationService(db)

    conversation = service.get_conversation(
        conversation_id
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    return conversation

@app.delete(
    "/conversations/{conversation_id}",
    tags=["Conversations"],
    summary="Soft delete a conversation"
)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):

    service = ConversationService(db)

    deleted = service.soft_delete_conversation(
        conversation_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    return {
        "status": "success",
        "message": "Conversation deleted successfully."
    }






# ---------------------------------------------------------
# PERMANENT DELETE — FUTURE ADMIN/BACKEND OPERATION
# ---------------------------------------------------------
#
# This endpoint is intentionally disabled for normal users.
#
# If we later need an admin-only permanent deletion API,
# it can call:
#
# service.permanently_delete_conversation(
#     conversation_id
# )
#
# This will permanently remove the conversation and its
# associated messages from the database.
#
# Example future endpoint:
#
""" @app.delete(
     "/admin/conversations/{conversation_id}/permanent",
     tags=["Admin"],
     summary="Permanently delete a conversation"
 )
 def permanently_delete_conversation(
     conversation_id: int,
     db: Session = Depends(get_db)
 ):

     service = ConversationService(db)

     deleted = service.permanently_delete_conversation(
         conversation_id
     )

     if not deleted:
         raise HTTPException(
             status_code=404,
             detail="Conversation not found."
         )

     return {
         "status": "success",
         "message": "Conversation permanently deleted."
     } """