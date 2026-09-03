from app.services.llm_service import LLMService
from app.services.vector_store import VectorStore
import app.services.reranker as Reranker

class RAGService:

    def __init__(self, vector_store, embedding_service):

        print("1. Creating RAGService")

        self.vector_store = vector_store
        self.embedding_service = embedding_service

        print("2. Creating LLMService")

        self.llm_service = LLMService()

        print("3. Creating Reranker")

        self.reranker = Reranker()

        print("4. RAGService created successfully")

    def ask(self, question: str, top_k: int = 3, source: str | None = None, section: str | None = None):

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
            retrieval_k = 10

            results = self.vector_store.search(
                query_vector,
                top_k=retrieval_k,
                source=source,
                section=section
            )
            print("FAISS RESULTS:", len(results))
            try:
                 results = self.reranker.rerank(
                      question,
                      results,
                      top_k=top_k
                      )
            except Exception as e:
                 print("RERANKER ERROR:", repr(e))
                 raise
            if not results:
                return {
                    "answer": "I could not find the answer in the provided documents.",
                    "sources": []
                    }
            print("\n===== RETRIEVAL RESULTS =====")
            for rank, result in enumerate(results, start=1):
                 print(f"\nRank: {rank}")
                 print(f"FAISS Distance: {result['distance']}")
                 print(f"Rerank Score: {result.get('rerank_score')}")
                 metadata = result["metadata"]
                 print(f"Source: {metadata.get('source')}")
                 
                 print(f"Text: {metadata.get('text')}")
                 print("=============================\n")

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