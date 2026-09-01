from pathlib import Path

from app.services.document_loader import load_document
from app.services.text_cleaner import clean_text
from app.services.chunker import chunk_text
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore


class IndexingService:

    def __init__(self, data_directory: str = "data"):
        self.data_directory = Path(data_directory)

        self.embedding_service = EmbeddingService()

        self.vector_store = None

    def build_index(self) -> dict:

        if not self.data_directory.exists():
            raise FileNotFoundError(
                f"Data directory not found: {self.data_directory}"
            )

        all_chunks = []

        # Step 1: Read documents
        for file_path in self.data_directory.iterdir():

            if not file_path.is_file():
                continue

            try:
                document = load_document(str(file_path))

                # Step 2: Clean extracted text
                cleaned_text = clean_text(document["text"])

                if not cleaned_text:
                    continue

                # Step 3: Split text into chunks
                chunks = chunk_text(cleaned_text)

                # Step 4: Attach source information
                for chunk in chunks:
                    all_chunks.append({
                        "source": document["source"],
                        "text": chunk
                    })

            except Exception as exc:
                print(
                    f"Failed to process {file_path.name}: {exc}"
                )

        if not all_chunks:
            raise ValueError(
                "No valid document chunks found."
            )

        # Step 5: Create embeddings
        texts = [
            chunk["text"]
            for chunk in all_chunks
        ]

        embeddings = self.embedding_service.embed_texts(
            texts
        )

        # Step 6: Create FAISS vector store
        dimension = len(embeddings[0])

        self.vector_store = VectorStore(dimension)

        # Step 7: Store vectors + metadata
        self.vector_store.add_vectors(
            embeddings,
            all_chunks
        )

        return {
            "documents": sum(
                1
                for file_path in self.data_directory.iterdir()
                if file_path.is_file()
                and file_path.suffix.lower() in {".txt", ".pdf", ".docx"}
                ),
            "chunks": len(all_chunks),
            "embedding_dimension": dimension
        }