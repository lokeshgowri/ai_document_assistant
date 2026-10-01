from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableParallel,
    RunnableLambda,
)
from langchain.chat_models import init_chat_model


def format_documents(
    documents: list[Document]
) -> str:

    formatted_documents = []

    for document in documents:

        source = document.metadata.get(
            "source",
            "Unknown source"
        )

        section = document.metadata.get(
            "section",
            "Unknown section"
        )

        formatted_documents.append(
            (
                f"Source: {source}\n"
                f"Section: {section}\n"
                f"Content:\n"
                f"{document.page_content}"
            )
        )

    return "\n\n---\n\n".join(
        formatted_documents
    )


def create_rag_chain(retriever):

    model = init_chat_model(
        "llama3.2",
        model_provider="ollama",
        num_ctx=4096,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a document question-answering assistant.

Answer the user's question using ONLY the information
provided in the retrieved documents.

Do not use general knowledge.
Do not make assumptions.
Do not add recommendations or opinions.

If the answer cannot be found in the retrieved documents,
say exactly:

"I could not find the answer in the provided documents."

Retrieved documents:

{context}
"""
            ),
            (
                "human",
                "{question}"
            ),
        ]
    )

    # ---------------------------------------------------------
    # 1. Retrieve documents only once
    # ---------------------------------------------------------

    retrieval = RunnableParallel(
        documents=retriever,
        question=RunnablePassthrough(),
    )

    # ---------------------------------------------------------
    # 2. Generate the answer using the retrieved documents
    # ---------------------------------------------------------

    answer_chain = (
        {
            "context": RunnableLambda(
                lambda data: format_documents(
                    data["documents"]
                )
            ),
            "question": RunnableLambda(
                lambda data: data["question"]
            ),
        }
        | prompt
        | model
    )

    # ---------------------------------------------------------
    # 3. Return both answer and retrieved documents
    # ---------------------------------------------------------

    rag_chain = (
        retrieval
        | RunnableParallel(
            answer=answer_chain,
            documents=RunnableLambda(
                lambda data: data["documents"]
            ),
        )
    )

    return rag_chain