from app.config import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K,
    LLM_API_KEY,
    EMBEDDING_MODEL,
)


print("LLM API Key:", LLM_API_KEY)
print("Embedding Model:", EMBEDDING_MODEL)
print("Chunk Size:", CHUNK_SIZE)
print("Chunk Overlap:", CHUNK_OVERLAP)
print("Top K:", TOP_K)