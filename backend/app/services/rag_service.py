from app.services.llm_service import LLMService
from app.services.vector_store import VectorStore
from app.services.keyword_search import KeywordSearch
from app.services.query_processor import QueryProcessor


class RAGService:

    def __init__(self, vector_store, embedding_service):

        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.llm_service = LLMService()
        self.query_processor = QueryProcessor()

        self.keyword_search = KeywordSearch(
            getattr(self.vector_store, "metadata", [])
        )

    def ask(
        self,
        question: str,
        top_k: int = 3,
        source: str | None = None,
        section: str | None = None,
        distance_threshold: float | None = None
    ) -> dict:

        if not question or not question.strip():

            raise ValueError(
                "Question cannot be empty."
            )

        if top_k <= 0:

            raise ValueError(
                "top_k must be greater than 0."
            )

        question = self.query_processor.process(
            question
        )

        try:

            # Convert question into an embedding
            query_vector = self.embedding_service.embed_text(
                question
            )

            # Retrieve semantic candidates using FAISS
            retrieval_k = 10

            if distance_threshold is None:

                distance_threshold = 0.9

            try:

                semantic_results = self.vector_store.search(
                    query_vector,
                    top_k=retrieval_k,
                    source=source,
                    section=section,
                    distance_threshold=distance_threshold
                )

            except TypeError:

                semantic_results = self.vector_store.search(
                    query_vector,
                    top_k=retrieval_k,
                    section=section
                )

            # Generate expanded queries for keyword search
            expanded_queries = self.query_processor.expand(
                question
            )

            # Retrieve keyword candidates using BM25
            keyword_results = []

            for expanded_query in expanded_queries:

                results = self.keyword_search.search(
                    expanded_query,
                    top_k=retrieval_k
                )

                keyword_results.extend(results)

            # Combine semantic and keyword results
            combined_results = []

            seen_chunks = set()

            for result in semantic_results:

                metadata = result["metadata"]

                chunk_id = metadata.get(
                    "chunk_id",
                    metadata.get("text")
                )

                if chunk_id not in seen_chunks:

                    result["retrieval_method"] = "semantic"

                    combined_results.append(result)

                    seen_chunks.add(chunk_id)

            for result in keyword_results:

                metadata = result["metadata"]

                chunk_id = metadata.get(
                    "chunk_id",
                    metadata.get("text")
                )

                if chunk_id not in seen_chunks:

                    result["retrieval_method"] = "keyword"

                    combined_results.append(result)

                    seen_chunks.add(chunk_id)

            # Apply source and section filters
            filtered_results = []

            for result in combined_results:

                metadata = result["metadata"]

                if source:

                    metadata_source = metadata.get(
                        "source"
                    )

                    if not metadata_source:
                        continue

                    if source.lower() not in metadata_source.lower():
                        continue

                if section:

                    metadata_section = metadata.get(
                        "section"
                    )

                    if not metadata_section:
                        continue

                    if section.lower() not in metadata_section.lower():
                        continue

                filtered_results.append(result)

            combined_results = filtered_results

            # No retrieved candidates
            if not combined_results:

                return {
                    "answer": (
                        "I could not find the answer "
                        "in the provided documents."
                    ),
                    "sources": []
                }

            results = combined_results[:top_k]

            # No results after reranking
            if not results:

                return {
                    "answer": (
                        "I could not find the answer "
                        "in the provided documents."
                    ),
                    "sources": []
                }

            # Build context with source and section metadata
            context_parts = []

            for result in results:

                metadata = result["metadata"]

                context_parts.append(
                    f"""
Source: {metadata.get("source")}
Section: {metadata.get("section", "Unknown")}

{metadata.get("text", "")}
""".strip()
                )

            context = "\n\n".join(
                context_parts
            )

            # Generate grounded answer
            answer = self.llm_service.generate_answer(
                question=question,
                context=context
            )

            # Handle the LLM no-answer response
            no_answer_message = (
                "I could not find the answer "
                "in the provided documents."
            )

            if answer.strip() == no_answer_message:

                return {
                    "answer": answer,
                    "sources": []
                }

            # Return answer and sources
            return {
                "answer": answer,
                "sources": [
                    result["metadata"]
                    for result in results
                ]
            }

        except ValueError:

            raise

        except Exception as exc:

            raise RuntimeError(
                "Failed to process the question."
            ) from exc