from app.services.rag_service import RAGService
from app.services.vector_store import VectorStore
from app.services.embeddings import EmbeddingService


# Create services
embedding_service = EmbeddingService()

# Sample document chunks
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


# Create embeddings
texts = [chunk["text"] for chunk in chunks]

embeddings = embedding_service.embed_texts(texts)


# Create vector store
dimension = len(embeddings[0])

vector_store = VectorStore(dimension)

vector_store.add_vectors(
    embeddings,
    chunks
)


# Create RAG service
rag_service = RAGService(
    vector_store=vector_store,
    embedding_service=embedding_service
)


questions = [
    "How many annual leave days are employees entitled to?",
    "Where should employees submit their leave requests?",
    "How many maternity leave days are employees entitled to?"
]


for question in questions:

    print("\n" + "=" * 60)

    print("QUESTION:")
    print(question)

    result = rag_service.ask(
        question=question,
        top_k=2
    )

    print("\nANSWER:")
    print(result["answer"])

    print("\nSOURCES:")
    for source in result["sources"]:
        print(source)