from app.services.rag_service import RAGService
from app.services.vector_store import VectorStore
from app.services.embeddings import EmbeddingService


# Create our services
embedding_service = EmbeddingService()

# Create a small sample knowledge base
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


# Create embeddings for the chunks
texts = [chunk["text"] for chunk in chunks]

embeddings = embedding_service.embed_texts(texts)


# Create FAISS vector store
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


# Ask a question
question = "What is the company's maternity leave policy?"

result = rag_service.ask(
    question=question,
    top_k=2,
    section=None
)


print("\nQUESTION:")
print(question)

print("\nANSWER:")
print(result["answer"])

print("\nSOURCES:")

for source in result["sources"]:
    print(source)