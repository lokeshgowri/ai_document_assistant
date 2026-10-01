from typing import Any

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever


class HybridRAGRetriever(BaseRetriever):

    rag_service: Any
    top_k: int = 3
    source: str | None = None
    section: str | None = None
    conversation_id: int | None = None
    conversation_history: list[dict] | None = None

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager=None,
    ) -> list[Document]:

        results = self.rag_service.retrieve_documents(
            question=query,
            top_k=self.top_k,
            source=self.source,
            section=self.section,
            conversation_id=self.conversation_id,
            conversation_history=self.conversation_history,
        )

        documents = []

        for result in results:

            metadata = result.get(
                "metadata",
                {}
            )

            text = metadata.get(
                "text",
                ""
            )

            document_metadata = {
                key: value
                for key, value in metadata.items()
                if key != "text"
            }

            documents.append(
                Document(
                    page_content=text,
                    metadata=document_metadata,
                )
            )

        return documents