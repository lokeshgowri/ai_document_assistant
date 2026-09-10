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
        distance_threshold: float | None = None,
        conversation_id: int | None = None
    ) -> dict:

        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        if conversation_id is None:
            raise ValueError("conversation_id is required.")

        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")

        question = self.query_processor.process(question)

        try:
            has_conversation_documents = any(
                metadata.get("conversation_id") == conversation_id
                for metadata in self.vector_store.metadata
            )

            query_vector = self.embedding_service.embed_text(question)

            retrieval_k = max(10, len(self.vector_store.metadata))

            if distance_threshold is None:
                distance_threshold = 0.9

            try:
                semantic_results = self.vector_store.search(
                    query_vector,
                    top_k=retrieval_k,
                    source=source,
                    section=section,
                    distance_threshold=distance_threshold,
                    conversation_id=(
                        conversation_id if has_conversation_documents else None
                    ),
                    global_only=(not has_conversation_documents)
                )
            except TypeError:
                semantic_results = self.vector_store.search(
                    query_vector,
                    top_k=retrieval_k,
                    section=section,
                    conversation_id=(
                        conversation_id if has_conversation_documents else None
                    ),
                    global_only=(not has_conversation_documents)
                )

            expanded_queries = self.query_processor.expand(question)

            keyword_results = []
            for expanded_query in expanded_queries:
                results = self.keyword_search.search(expanded_query, top_k=retrieval_k)
                keyword_results.extend(results)

            combined_results = []
            seen_chunks = set()

            for result in semantic_results:
                metadata = result["metadata"]
                metadata_conversation_id = metadata.get("conversation_id")

                if has_conversation_documents:
                    if metadata_conversation_id != conversation_id:
                        continue
                else:
                    if metadata_conversation_id is not None:
                        continue

                chunk_id = metadata.get("chunk_id", metadata.get("text"))

                if chunk_id not in seen_chunks:
                    result["retrieval_method"] = "semantic"
                    combined_results.append(result)
                    seen_chunks.add(chunk_id)

            for result in keyword_results:
                metadata = result["metadata"]
                metadata_conversation_id = metadata.get("conversation_id")

                if has_conversation_documents:
                    if metadata_conversation_id != conversation_id:
                        continue
                else:
                    if metadata_conversation_id is not None:
                        continue

                chunk_id = metadata.get("chunk_id", metadata.get("text"))

                if chunk_id not in seen_chunks:
                    result["retrieval_method"] = "keyword"
                    combined_results.append(result)
                    seen_chunks.add(chunk_id)

            filtered_results = []
            for result in combined_results:
                metadata = result["metadata"]

                if source:
                    metadata_source = metadata.get("source")
                    if not metadata_source:
                        continue
                    if source.lower() not in metadata_source.lower():
                        continue

                if section:
                    metadata_section = metadata.get("section")
                    if not metadata_section:
                        continue
                    if section.lower() not in metadata_section.lower():
                        continue

                filtered_results.append(result)

            combined_results = filtered_results

            if not combined_results:
                return {
                    "answer": "I could not find the answer in the provided documents.",
                    "sources": []
                }

            results = combined_results[:top_k]

            if not results:
                return {
                    "answer": "I could not find the answer in the provided documents.",
                    "sources": []
                }

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

            context = "\n\n".join(context_parts)

            answer = self.llm_service.generate_answer(
                question=question,
                context=context
            )

            no_answer_message = "I could not find the answer in the provided documents."

            if answer.strip() == no_answer_message:
                return {"answer": answer, "sources": []}

            unique_sources = []
            seen_sources = set()

            for result in results:
                metadata = result["metadata"]
                source_name = metadata.get("source")

                if not source_name:
                    continue
                if source_name in seen_sources:
                    continue

                seen_sources.add(source_name)
                unique_sources.append({
                    "source": source_name,
                    "text": metadata.get("text", "")
                })

            return {
                "answer": answer,
                "sources": unique_sources
            }

        except ValueError:
            raise

        except Exception as exc:
            raise RuntimeError("Failed to process the question.") from exc