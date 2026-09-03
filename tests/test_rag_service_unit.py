from app.services.rag_service import RAGService


class FakeEmbeddingService:

    def embed_text(self, text):
        return [1.0, 0.0, 0.0]


class FakeVectorStore:

    def search(self, query_vector, top_k=3,section=None):

        return [
            {
                "distance": 0.1,
                "metadata": {
                    "source": "sample.txt",
                    "text": "Employees are entitled to 15 days of paid leave per year."
                }
            }
        ]


class FakeLLMService:

    def generate_answer(self, question, context):

        return "Employees are entitled to 15 days of paid leave per year."


def test_rag_service_ask():

    embedding_service = FakeEmbeddingService()
    vector_store = FakeVectorStore()

    rag_service = RAGService(
        vector_store=vector_store,
        embedding_service=embedding_service
    )

    # Replace the real LLM with our fake LLM
    rag_service.llm_service = FakeLLMService()

    result = rag_service.ask(
        question="How many paid leave days do employees get?",
        top_k=3,
        section=None
    )

    assert result["answer"] == (
        "Employees are entitled to 15 days of paid leave per year."
    )

    assert len(result["sources"]) == 1

    assert result["sources"][0]["source"] == "sample.txt"

def test_rag_service_empty_question():

    embedding_service = FakeEmbeddingService()
    vector_store = FakeVectorStore()

    rag_service = RAGService(
        vector_store=vector_store,
        embedding_service=embedding_service
    )

    try:
        rag_service.ask(
            question="",
            top_k=3,
            section=None
        )

        assert False, "Expected ValueError"

    except ValueError as exc:
        assert str(exc) == "Question cannot be empty."


def test_rag_service_invalid_top_k():

    embedding_service = FakeEmbeddingService()
    vector_store = FakeVectorStore()

    rag_service = RAGService(
        vector_store=vector_store,
        embedding_service=embedding_service
    )

    try:
        rag_service.ask(
            question="What is the leave policy?",
            top_k=0,
            section=None
        )

        assert False, "Expected ValueError"

    except ValueError as exc:
        assert str(exc) == "top_k must be greater than 0."