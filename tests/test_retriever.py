from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore


embedding_service = EmbeddingService()


chunks = [
    {
        "source": "sample.txt",
        "text": "Employees are entitled to 20 days of annual leave per year."
    },
    {
        "source": "sample.txt",
        "text": "Employees should submit leave requests through the HR portal."
    },
    {
        "source": "sample.txt",
        "text": "Leave requests should be submitted at least three working days in advance."
    }
]


texts = [chunk["text"] for chunk in chunks]

embeddings = embedding_service.embed_texts(texts)

dimension = len(embeddings[0])

store = VectorStore(dimension)

store.add_vectors(
    embeddings,
    chunks
)


questions = [
    "How many annual leave days are employees entitled to?",
    "How much vacation time does an employee receive?",
    "Where should employees submit their leave request?",
    "Which system should be used to request leave?",
    "How early should employees apply for leave?",
    "How many working days in advance is leave required?",
    "What is the company's health insurance policy?",
    "Can employees submit leave requests through email?"
]


for question in questions:

    query_vector = embedding_service.embed_text(question)

    results = store.search(
        query_vector,
        top_k=2
    )

    print("\n" + "=" * 60)
    print("QUESTION:", question)
    print("=" * 60)

    for result in results:
        print("\nDistance:", result["distance"])
        print("Source:", result["metadata"]["source"])
        print("Text:", result["metadata"]["text"])