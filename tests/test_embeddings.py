from sentence_transformers import util

from app.services.embeddings import EmbeddingService


embedding_service = EmbeddingService()

texts = [
    "Employees receive 20 days of annual leave.",
    "Workers get twenty days of vacation each year.",
    "The company provides health insurance."
]

embeddings = embedding_service.model.encode(texts)

similarity_1 = util.cos_sim(embeddings[0], embeddings[1])
similarity_2 = util.cos_sim(embeddings[0], embeddings[2])

print("Leave vs vacation:", similarity_1)
print("Leave vs health insurance:", similarity_2)