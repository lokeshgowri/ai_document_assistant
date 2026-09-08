from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    Depends
)
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
from app.services.blob_service import BlobStorageService


# ---------------------------------------------------------
# GLOBAL SERVICES
# ---------------------------------------------------------

embedding_service = EmbeddingService()

indexing_service = IndexingService()

blob_service = BlobStorageService()

rag_service = None


# ---------------------------------------------------------
# APPLICATION STARTUP / SHUTDOWN
# ---------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    global rag_service

    try:

        saved_vector_store = (
            await indexing_service.load_persisted_index()
        )

        if saved_vector_store is not None:

            rag_service = RAGService(
                vector_store=saved_vector_store,
                embedding_service=(
                    indexing_service.embedding_service
                )
            )

            print(
                "Persisted FAISS index loaded from Blob."
            )

        else:

            print(
                "No persisted FAISS index found in Blob."
            )

    except Exception as exc:

        print(
            f"STARTUP INDEX LOAD ERROR: {exc}"
        )

        rag_service = None

    yield


# ---------------------------------------------------------
# FASTAPI APPLICATION
# ---------------------------------------------------------

app = FastAPI(
    title="AI Document Q&A Assistant",
    description=(
        "A Retrieval-Augmented Generation (RAG) API "
        "for answering questions from indexed documents "
        "using semantic search, keyword search, "
        "and a grounded language model."
    ),
    version="1.0.0",
    lifespan=lifespan
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        " https://lokeshgowri.github.io/ai-document-qa-assistant_fe/",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# ROOT
# ---------------------------------------------------------

@app.get(
    "/",
    tags=["System"],
    summary="Check API availability"
)
def root():

    return {
        "message": (
            "AI Document Q&A Assistant is running."
        )
    }


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@app.get(
    "/health",
    tags=["System"],
    summary="Check application health"
)
def health_check():

    return {
        "status": "ok"
    }


# ---------------------------------------------------------
# ASK QUESTION
# ---------------------------------------------------------

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

    global rag_service

    # -----------------------------------------------------
    # Check whether index is available
    # -----------------------------------------------------

    if rag_service is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Documents have not been indexed yet. "
                "Please call /index first."
            )
        )

    conversation_service = ConversationService(db)

    # -----------------------------------------------------
    # 1. Validate conversation
    # -----------------------------------------------------

    if request.conversation_id is not None:

        conversation = (
            conversation_service.get_conversation(
                request.conversation_id
            )
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

    # -----------------------------------------------------
    # 2. Run RAG pipeline
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # 3. Save assistant response
    # -----------------------------------------------------

    if request.conversation_id is not None:

        conversation_service.add_message(
            conversation_id=request.conversation_id,
            role="assistant",
            content=response["answer"]
        )

    # -----------------------------------------------------
    # 4. Return RAG response
    # -----------------------------------------------------

    return response


# ---------------------------------------------------------
# INDEX DOCUMENTS
# ---------------------------------------------------------

@app.post(
    "/index",
    tags=["Documents"],
    summary="Index documents"
)
async def index_documents():

    global rag_service

    try:

        result = (
            await indexing_service.build_index()
        )

        rag_service = RAGService(
            vector_store=(
                indexing_service.vector_store
            ),
            embedding_service=(
                indexing_service.embedding_service
            )
        )

        return {

            "status": "success",

            "message": (
                "Documents indexed successfully."
            ),

            "details": result

        }

    except Exception as exc:

        print(
            f"INDEX ERROR: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to index documents."
        )


# ---------------------------------------------------------
# INDEX STATUS
# ---------------------------------------------------------

@app.get(
    "/index/status",
    tags=["Documents"],
    summary="Get current index status"
)
async def get_index_status():

    return (
        await indexing_service.get_index_status()
    )


# ---------------------------------------------------------
# UPLOAD DOCUMENT
# ---------------------------------------------------------

@app.post(
    "/upload",
    tags=["Documents"],
    summary="Upload a document"
)
async def upload_document(
    file: UploadFile = File(...)
):

    try:

        # Read uploaded file
        file_bytes = await file.read()

        # Preserve original filename
        pathname = (
            f"documents/{file.filename}"
        )

        # Upload document to Vercel Blob
        blob = await blob_service.upload_file(
            pathname=pathname,
            data=file_bytes,
            content_type=file.content_type,
            overwrite=True
        )

        return {

            "status": "success",

            "message": (
                "Document uploaded successfully."
            ),

            "filename": file.filename,

            "pathname": blob.pathname,

            "url": blob.url

        }

    except Exception as exc:

        print(
            f"UPLOAD ERROR: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to upload document."
        )


# ---------------------------------------------------------
# CREATE CONVERSATION
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# GET ALL CONVERSATIONS
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# GET SINGLE CONVERSATION
# ---------------------------------------------------------

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

    conversation = (
        service.get_conversation(
            conversation_id
        )
    )

    if not conversation:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    return conversation


# ---------------------------------------------------------
# DELETE CONVERSATION
# ---------------------------------------------------------

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

    deleted = (
        service.soft_delete_conversation(
            conversation_id
        )
    )

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    return {

        "status": "success",

        "message": (
            "Conversation deleted successfully."
        )

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
"""
@app.delete(
    "/admin/conversations/{conversation_id}/permanent",
    tags=["Admin"],
    summary="Permanently delete a conversation"
)
def permanently_delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):

    service = ConversationService(db)

    deleted = (
        service.permanently_delete_conversation(
            conversation_id
        )
    )

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    return {

        "status": "success",

        "message": (
            "Conversation permanently deleted."
        )

    }
"""