from app.services.langchain_retriever import (
    HybridRAGRetriever
)

from langchain_core.documents import Document


class FakeRAGService:

    def retrieve_documents(
        self,
        question,
        top_k,
        source,
        section,
        conversation_id,
        conversation_history,
    ):

        return [
            {
                "distance": 0.25,
                "metadata": {
                    "source": "handbook.pdf",
                    "section": "Leave Policy",
                    "text": (
                        "Employees receive annual leave."
                    ),
                    "chunk_id": "abc_chunk_1",
                    "conversation_id": conversation_id,
                },
            }
        ]


def test_retriever_returns_documents():

    rag_service = FakeRAGService()

    retriever = HybridRAGRetriever(
        rag_service=rag_service,
        top_k=3,
        conversation_id=1,
    )

    documents = retriever.invoke(
        "What is the leave policy?"
    )

    assert len(documents) == 1

    assert isinstance(
        documents[0],
        Document
    )

    assert (
        documents[0].page_content
        == "Employees receive annual leave."
    )

    assert (
        documents[0].metadata["source"]
        == "handbook.pdf"
    )

    assert (
        documents[0].metadata["section"]
        == "Leave Policy"
    )