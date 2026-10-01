from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda

from app.services.langchain_rag_chain import (
    create_rag_chain
)


def fake_retriever(question):

    return [
        Document(
            page_content=(
                "Employees receive 20 days "
                "of annual leave."
            ),
            metadata={
                "source": "handbook.pdf",
                "section": "Leave Policy",
            },
        )
    ]


retriever = RunnableLambda(
    fake_retriever
)

chain = create_rag_chain(
    retriever
)

response = chain.invoke(
    "How many annual leave days do employees receive?"
)

print(response.content)