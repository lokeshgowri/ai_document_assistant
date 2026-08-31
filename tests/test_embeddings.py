from app.services.embeddings import EmbeddingService


embedding_service = EmbeddingService()


# Test single text
text = "Employees are entitled to 20 days of annual leave per year."

vector = embedding_service.embed_text(text)

print("\nSINGLE TEXT")
print("Vector type:", type(vector))
print("Vector length:", len(vector))
print("First 5 values:", vector[:5])


# Test multiple texts
texts = [
    "Employees are entitled to 20 days of annual leave per year.",
    "Employees should submit leave requests through the HR portal.",
    "Leave requests should be submitted at least three working days in advance."
]

vectors = embedding_service.embed_texts(texts)

print("\nMULTIPLE TEXTS")
print("Number of vectors:", len(vectors))
print("Vector length:", len(vectors[0]))