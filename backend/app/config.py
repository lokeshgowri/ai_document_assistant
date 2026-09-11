import os

from dotenv import load_dotenv


load_dotenv()


# --------------------------------------------------
# Provider Configuration
# --------------------------------------------------

LLM_PROVIDER = os.getenv(
    "LLM_PROVIDER",
    "gemini"
).lower()

EMBEDDING_PROVIDER = os.getenv(
    "EMBEDDING_PROVIDER",
    "gemini"
).lower()


# --------------------------------------------------
# API Configuration
# --------------------------------------------------

LLM_API_KEY = os.getenv("LLM_API_KEY")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# --------------------------------------------------
# Model Configuration
# --------------------------------------------------

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "gemini-3.6-flash"
)


# --------------------------------------------------
# Ollama Configuration
# --------------------------------------------------

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434"
)

OLLAMA_LLM_MODEL = os.getenv(
    "OLLAMA_LLM_MODEL",
    "llama3.2"
)

OLLAMA_EMBEDDING_MODEL = os.getenv(
    "OLLAMA_EMBEDDING_MODEL",
    "nomic-embed-text"
)


# --------------------------------------------------
# RAG Configuration
# --------------------------------------------------

CHUNK_SIZE = int(
    os.getenv("CHUNK_SIZE", "500")
)

CHUNK_OVERLAP = int(
    os.getenv("CHUNK_OVERLAP", "50")
)

TOP_K = int(
    os.getenv("TOP_K", "5")
)