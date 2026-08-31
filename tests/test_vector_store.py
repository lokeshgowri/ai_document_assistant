from app.services.vector_store import VectorStore


dimension = 3

vectors = [
    [1.0, 0.0, 0.0],
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0],
]

metadata = [
    {
        "source": "leave_policy.txt",
        "text": "Employees receive 20 days of annual leave."
    },
    {
        "source": "hr_policy.txt",
        "text": "Leave requests must be submitted through HR."
    },
    {
        "source": "benefits.txt",
        "text": "The company provides health insurance."
    },
]


store = VectorStore(dimension)

store.add_vectors(vectors, metadata)

print("Number of vectors:", store.index.ntotal)
print("Metadata:", store.metadata)

store.save("data/index.faiss")

print("Index saved successfully.")

new_store = VectorStore(dimension)

new_store.load("data/index.faiss")

print(
    "Loaded vectors:",
    new_store.index.ntotal
)