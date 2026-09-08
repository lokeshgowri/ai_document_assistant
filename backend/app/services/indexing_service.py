from pathlib import Path
import tempfile

from app.services.blob_index_store import BlobIndexStore
from app.services.blob_service import BlobStorageService
from app.services.chunker import chunk_text_with_metadata
from app.services.document_loader import load_document
from app.services.embeddings import EmbeddingService
from app.services.text_cleaner import clean_text
from app.services.vector_store import VectorStore


class IndexingService:

    def __init__(self, data_directory: str = "data"):

        self.data_directory = Path(
            data_directory
        )

        self.embedding_service = EmbeddingService()

        self.blob_service = BlobStorageService()

        self.blob_index_store = BlobIndexStore()

        self.vector_store = None

        self.supported_extensions = {
            ".txt",
            ".pdf",
            ".docx"
        }

    async def _download_blob_to_temp_file(
        self,
        pathname: str
    ) -> Path:

        result = await self.blob_service.get_file(
            pathname
        )

        if result is None:

            raise FileNotFoundError(
                f"Blob not found: {pathname}"
            )

        blob_bytes = result.content

        suffix = (
            Path(pathname)
            .suffix
            .lower()
        )

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        )

        temp_path = Path(
            temp_file.name
        )

        try:

            temp_file.write(
                blob_bytes
            )

            temp_file.close()

            return temp_path

        except Exception:

            temp_file.close()

            if temp_path.exists():

                temp_path.unlink()

            raise

    async def build_index(self) -> dict:

        all_chunks = []

        processed_documents = 0

        blobs = await self.blob_service.list_files(
            prefix="documents/"
        )

        for blob in blobs.blobs:

            pathname = blob.pathname

            extension = (
                Path(pathname)
                .suffix
                .lower()
            )

            if extension not in self.supported_extensions:

                continue

            temp_path = None

            try:

                temp_path = (
                    await self._download_blob_to_temp_file(
                        pathname
                    )
                )

                document = load_document(
                    str(temp_path)
                )

                cleaned_text = clean_text(
                    document["text"]
                )

                if not cleaned_text:

                    continue

                chunks = chunk_text_with_metadata(
                    cleaned_text
                )

                source_name = (
                    Path(pathname).name
                )

                for chunk_index, chunk in enumerate(
                    chunks
                ):

                    all_chunks.append({

                        "source": source_name,

                        "section": chunk["section"],

                        "document_type": (
                            extension
                            .lstrip(".")
                        ),

                        "chunk_id": (
                            f"{source_name}"
                            f"_chunk_{chunk_index}"
                        ),

                        "text": chunk["text"]

                    })

                if chunks:

                    processed_documents += 1

            except Exception as exc:

                print(
                    f"INDEX DOCUMENT ERROR "
                    f"({pathname}): {exc}"
                )

            finally:

                if (
                    temp_path is not None
                    and temp_path.exists()
                ):

                    temp_path.unlink()

        if not all_chunks:

            raise ValueError(
                "No valid document chunks found."
            )

        texts = [
            chunk["text"]
            for chunk in all_chunks
        ]

        embeddings = (
            self.embedding_service.embed_texts(
                texts
            )
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

        await self.blob_index_store.save(
            self.vector_store
        )

        return {

            "documents": processed_documents,

            "chunks": len(all_chunks),

            "embedding_dimension": dimension

        }

    async def load_persisted_index(self):

        vector_store = (
            await self.blob_index_store.load()
        )

        if vector_store is None:

            return None

        self.vector_store = vector_store

        return vector_store

    async def get_index_status(self) -> dict:

        try:

            metadata = (
                await self.blob_index_store.get_metadata()
            )

            if metadata is None:

                return {

                    "indexed": False,

                    "documents": 0,

                    "chunks": 0

                }

            unique_documents = {

                item["source"]

                for item in metadata

                if item.get("source")

            }

            return {

                "indexed": True,

                "documents": len(
                    unique_documents
                ),

                "chunks": len(
                    metadata
                )

            }

        except Exception as exc:

            print(
                f"INDEX STATUS ERROR: {exc}"
            )

            return {

                "indexed": False,

                "documents": 0,

                "chunks": 0

            }