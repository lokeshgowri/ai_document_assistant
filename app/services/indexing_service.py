from pathlib import Path

from app.services.chunker import chunk_text_with_metadata
from app.services.document_loader import load_document
from app.services.embeddings import EmbeddingService
from app.services.text_cleaner import clean_text
from app.services.vector_store import VectorStore


class IndexingService:

    def __init__(self, data_directory: str = "data"):

        self.data_directory = Path(data_directory)

        self.embedding_service = EmbeddingService()

        self.vector_store = None

        self.index_path = (
            self.data_directory / "index.faiss"
        )

        self.supported_extensions = {
            ".txt",
            ".pdf",
            ".docx"
        }

    def build_index(self) -> dict:

        if not self.data_directory.exists():

            raise FileNotFoundError(
                f"Data directory not found: {self.data_directory}"
            )

        all_chunks = []
        processed_documents = 0

        for file_path in self.data_directory.iterdir():

            if not file_path.is_file():
                continue

            if file_path.suffix.lower() not in self.supported_extensions:
                continue

            try:

                document = load_document(
                    str(file_path)
                )

                cleaned_text = clean_text(
                    document["text"]
                )

                if not cleaned_text:
                    continue

                chunks = chunk_text_with_metadata(
                    cleaned_text
                )

                for chunk_index, chunk in enumerate(chunks):

                    source_path = Path(
                        document["source"]
                    )

                    all_chunks.append({
                        "source": document["source"],
                        "section": chunk["section"],
                        "document_type": (
                            source_path
                            .suffix
                            .lower()
                            .lstrip(".")
                        ),
                        "chunk_id": (
                            f"{source_path.name}"
                            f"_chunk_{chunk_index}"
                        ),
                        "text": chunk["text"]
                    })

                if chunks:
                    processed_documents += 1

            except Exception:
                continue

        if not all_chunks:

            raise ValueError(
                "No valid document chunks found."
            )

        texts = [
            chunk["text"]
            for chunk in all_chunks
        ]

        embeddings = self.embedding_service.embed_texts(
            texts
        )

        dimension = len(
            embeddings[0]
        )

        self.vector_store = VectorStore(
            dimension
        )

        self.vector_store.add_vectors(
            embeddings,
            all_chunks
        )

        self.vector_store.save(
            str(self.index_path)
        )

        return {
            "documents": processed_documents,
            "chunks": len(all_chunks),
            "embedding_dimension": dimension
        }