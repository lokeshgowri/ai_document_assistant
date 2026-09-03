from pathlib import Path

from docx import document

from app.services.document_loader import load_document
from app.services.text_cleaner import clean_text
from app.services.chunker import chunk_text_with_metadata
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore


class IndexingService:

    def __init__(self, data_directory: str = "data"):
        self.data_directory = Path(data_directory)

        self.embedding_service = EmbeddingService()

        self.vector_store = None

        # Path where FAISS index will be saved
        self.index_path = self.data_directory / "index.faiss"

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

        # Step 1: Read documents
        for file_path in self.data_directory.iterdir():

            if not file_path.is_file():
                continue

            # Process only supported document types
            if file_path.suffix.lower() not in self.supported_extensions:
                continue

            try:
                document = load_document(str(file_path))

                # Step 2: Clean extracted text
                cleaned_text = clean_text(document["text"])

                if not cleaned_text:
                    continue

                # Step 3: Split text into chunks
                cleaned_text = clean_text(document["text"])

                chunks = chunk_text_with_metadata(cleaned_text)
                for chunk_index, chunk in enumerate(chunks):
                     file_path = Path(document["source"])
                     all_chunks.append({
                          "source": document["source"],
                          "section": chunk["section"],
                          "document_type": file_path.suffix.lower().lstrip("."),
                          "chunk_id": f"{file_path.name}_chunk_{chunk_index}",
                          "text": chunk["text"]
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

        # Step 8: Save FAISS index + metadata
        self.vector_store.save(
            str(self.index_path)
        )

        return {
            "documents": sum(
                1
                for file_path in self.data_directory.iterdir()
                if file_path.is_file()
                and file_path.suffix.lower() in self.supported_extensions
            ),
            "chunks": len(all_chunks),
            "embedding_dimension": dimension
        }