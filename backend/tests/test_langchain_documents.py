from langchain_core.documents import Document

from app.services.indexing_service import IndexingService


def test_create_langchain_documents():

    chunks = [
        {
            "section": "Leave Policy",
            "text": "Employees receive annual leave."
        },
        {
            "section": "Working Hours",
            "text": "Employees work eight hours per day."
        }
    ]

    documents = IndexingService._create_langchain_documents(
        chunks=chunks,
        source_name="employee_handbook.pdf",
        pathname="documents/employee_handbook.pdf",
        document_hash="abc123",
        document_type="pdf",
        conversation_id=None,
    )

    assert len(documents) == 2

    assert isinstance(
        documents[0],
        Document
    )

    assert (
        documents[0].page_content
        == "Employees receive annual leave."
    )

    assert (
        documents[0].metadata["section"]
        == "Leave Policy"
    )

    assert (
        documents[0].metadata["source"]
        == "employee_handbook.pdf"
    )