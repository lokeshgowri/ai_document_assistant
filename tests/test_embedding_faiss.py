from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore


# Create embedding service
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


# Extract text from chunks
texts = [
    chunk["text"]
    for chunk in chunks
]


# Create embeddings using nomic-embed-text
embeddings = embedding_service.embed_texts(texts)


print("\nEMBEDDINGS")
print("Number of vectors:", len(embeddings))
print("Vector dimension:", len(embeddings[0]))


# Create FAISS vector store
dimension = len(embeddings[0])

vector_store = VectorStore(dimension)


# Add vectors to FAISS
vector_store.add_vectors(
    embeddings,
    chunks
)


print("\nFAISS INDEX")
print("Number of stored vectors:", vector_store.index.ntotal)


# Create query embedding
question = "How many annual leave days do employees get?"

query_vector = embedding_service.embed_text(question)


# Search FAISS
results = vector_store.search(
    query_vector,
    top_k=2
)


print("\nSEARCH RESULTS")

for result in results:
    print(result)