from fastapi.testclient import TestClient

from app.main import app
from app.services.langchain_retriever import (
    HybridRAGRetriever
)
from app.services.langchain_rag_chain import (
    create_rag_chain
)


def test_real_langchain_rag():

    with TestClient(app) as client:

        # -------------------------------------------------
        # Get existing conversations
        # -------------------------------------------------

        response = client.get(
            "/conversations"
        )

        assert response.status_code == 200

        conversations = response.json()

        assert conversations

        print("\nCONVERSATIONS:")
        print(conversations)

        # -------------------------------------------------
        # Get the initialized RAG service
        # -------------------------------------------------

        from app.main import rag_service

        assert rag_service is not None

        # -------------------------------------------------
        # Use an existing conversation
        # -------------------------------------------------

        conversation_id = conversations[0]["id"]

        print(
            "\nUSING CONVERSATION:",
            conversation_id
        )

        # -------------------------------------------------
        # Create LangChain retriever
        # -------------------------------------------------

        retriever = HybridRAGRetriever(
            rag_service=rag_service,
            top_k=3,
            conversation_id=conversation_id,
        )

        # -------------------------------------------------
        # Create LangChain RAG chain
        # -------------------------------------------------

        chain = create_rag_chain(
            retriever
        )

        # -------------------------------------------------
        # Ask a real question
        # -------------------------------------------------

        question = (
            "What is the grievance procedure?"
        )

        response = chain.invoke(
            question
        )
        documents = response["documents"]

        sources = []

        for document in documents:
            sources.append(
        {
            "source": document.metadata.get(
                "source",
                "Unknown"
            ),
            "text": document.page_content,
        }
    )

        print("\nCONVERTED SOURCES:")

        for source in sources:
            print(source)

        print("\nQUESTION:")
        print(question)

        print("\nANSWER:")
        print(response["answer"].content)

        print("\nRETRIEVED DOCUMENTS:")

        for document in response["documents"]:
            print("\nSOURCE:", document.metadata.get("source"))
            print("SECTION:", document.metadata.get("section"))
            print("CHUNK:", document.metadata.get("chunk_id"))
            print("CONTENT:", document.page_content)

        # -------------------------------------------------
        # Basic validation
        # -------------------------------------------------

        assert response["answer"].content
        assert response["documents"]