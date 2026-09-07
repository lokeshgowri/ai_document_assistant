from app.services.vector_store import VectorStore


def test_vector_store_add_and_search():

    vector_store = VectorStore(dimension=3)

    vectors = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]

    metadata = [
        {
            "source": "document1.txt",
            "text": "Python is a programming language."
        },
        {
            "source": "document2.txt",
            "text": "FastAPI is a Python web framework."
        },
        {
            "source": "document3.txt",
            "text": "FAISS is used for vector similarity search."
        }
    ]

    vector_store.add_vectors(
        vectors,
        metadata
    )

    query_vector = [0.9, 0.1, 0.0]

    results = vector_store.search(
        query_vector,
        top_k=1
    )

    assert len(results) == 1

    assert results[0]["metadata"]["source"] == "document1.txt"

    assert (
        results[0]["metadata"]["text"]
        == "Python is a programming language."
    )