from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda

from app.services.langchain_rag_chain import (
    format_documents
)


def test_format_documents():

    documents = [
        Document(
            page_content=(
                "Employees receive 20 days "
                "of annual leave."
            ),
            metadata={
                "source": "handbook.pdf",
                "section": "Leave Policy",
            },
        ),
        Document(
            page_content=(
                "Employees receive 10 days "
                "of sick leave."
            ),
            metadata={
                "source": "handbook.pdf",
                "section": "Sick Leave",
            },
        ),
    ]

    result = format_documents(
        documents
    )

    assert "handbook.pdf" in result
    assert "Leave Policy" in result
    assert "20 days" in result
    assert "Sick Leave" in result
    assert "10 days" in result