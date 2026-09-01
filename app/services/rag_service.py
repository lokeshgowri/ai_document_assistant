from app.services.llm_service import LLMService
from app.services.vector_store import VectorStore

class RAGService:

    def __init__(self, vector_store, embedding_service):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.llm_service = LLMService()

    def ask(self, question: str, top_k: int = 3):

        # Validate question
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        # Validate top_k
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")

        try:
            # Step 1: Convert question into a vector
            query_vector = self.embedding_service.embed_text(question)

            # Step 2: Search FAISS
            results = self.vector_store.search(
                query_vector,
                top_k=top_k
            )

            # Step 3: Handle no results
            if not results:
                return {
                    "answer": "I could not find the answer in the provided documents.",
                    "sources": []
                }

            # Step 4: Extract retrieved text
            context_parts = []

            for result in results:
                context_parts.append(
                    result["metadata"]["text"]
                )

            context = "\n\n".join(context_parts)

            # Step 5: Generate answer using LLM
            answer = self.llm_service.generate_answer(
                question=question,
                context=context
            )

            # Step 6: Return answer and sources
            sources = []
        
            for result in results:
                source = result["metadata"].get("source")
                if source and source not in sources:
                    sources.append(source)
            return {
                "answer": answer,
                "sources": [
        result["metadata"]
        for result in results
    ]
}

        except Exception as exc:
            raise RuntimeError(
                "Failed to process the question."
            ) from exc