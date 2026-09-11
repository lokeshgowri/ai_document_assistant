from pathlib import Path
import hashlib
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
        self.data_directory = Path(data_directory)

        self.embedding_service = EmbeddingService()
        self.blob_service = BlobStorageService()
        self.blob_index_store = BlobIndexStore()

        self.vector_store = None

        self.supported_extensions = {
            ".txt",
            ".pdf",
            ".docx",
        }

    # ---------------------------------------------------------
    # DOWNLOAD BLOB
    # ---------------------------------------------------------

    async def _download_blob_to_temp_file(
        self,
        pathname: str,
    ) -> Path:

        result = await self.blob_service.get_file(pathname)

        if result is None:
            raise FileNotFoundError(
                f"Blob not found: {pathname}"
            )

        blob_bytes = result.content

        suffix = Path(pathname).suffix.lower()

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        )

        temp_path = Path(temp_file.name)

        try:
            temp_file.write(blob_bytes)
            temp_file.close()

            return temp_path

        except Exception:
            temp_file.close()

            if temp_path.exists():
                temp_path.unlink()

            raise

    # ---------------------------------------------------------
    # CALCULATE SHA-256 HASH
    # ---------------------------------------------------------

    @staticmethod
    def _calculate_file_hash(file_path: Path) -> str:

        sha256 = hashlib.sha256()

        with open(
            file_path,
            "rb"
        ) as file:

            for chunk in iter(
                lambda: file.read(1024 * 1024),
                b""
            ):
                sha256.update(chunk)

        return sha256.hexdigest()

    # ---------------------------------------------------------
    # DETERMINE DOCUMENT SCOPE
    # ---------------------------------------------------------

    @staticmethod
    def _get_conversation_id(
        pathname: str,
    ):

        path_parts = Path(pathname).parts

        # Global document:
        # documents/{filename}
        if len(path_parts) == 2:
            return None

        # Conversation document:
        # documents/{conversation_id}/{filename}
        if len(path_parts) == 3:

            try:
                return int(path_parts[1])

            except ValueError:
                return None

        return None

    # ---------------------------------------------------------
    # BUILD INDEX
    #
    # This remains available for a complete rebuild.
    # ---------------------------------------------------------

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

            path_parts = Path(pathname).parts

            if len(path_parts) == 2:

                conversation_id = None

            elif len(path_parts) == 3:

                try:
                    conversation_id = int(
                        path_parts[1]
                    )

                except ValueError:
                    print(
                        f"SKIPPING INVALID DOCUMENT PATH: "
                        f"{pathname}"
                    )
                    continue

            else:

                print(
                    f"SKIPPING INVALID DOCUMENT PATH: "
                    f"{pathname}"
                )
                continue

            temp_path = None

            try:

                temp_path = (
                    await self._download_blob_to_temp_file(
                        pathname
                    )
                )

                document_hash = (
                    self._calculate_file_hash(
                        temp_path
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

                source_name = Path(
                    pathname
                ).name

                for chunk_index, chunk in enumerate(
                    chunks
                ):

                    all_chunks.append(
                        {
                            "source": source_name,
                            "document_path": pathname,
                            "document_hash": document_hash,
                            "section": chunk["section"],
                            "document_type": (
                                extension.lstrip(".")
                            ),
                            "chunk_id": (
                                f"{document_hash}"
                                f"_chunk_{chunk_index}"
                            ),
                            "text": chunk["text"],
                            "conversation_id": conversation_id,
                        }
                    )

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
                "No valid documents found to index."
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
            "embedding_dimension": dimension,
        }

    # ---------------------------------------------------------
    # INCREMENTAL INDEX
    # ---------------------------------------------------------

    async def incremental_index(
        self,
        pathname: str,
    ) -> dict:

        extension = (
            Path(pathname)
            .suffix
            .lower()
        )

        if extension not in self.supported_extensions:

            raise ValueError(
                f"Unsupported file type: {extension}"
            )

        conversation_id = (
            self._get_conversation_id(
                pathname
            )
        )

        # -----------------------------------------------------
        # Make sure a vector store exists
        # -----------------------------------------------------

        if self.vector_store is None:

            self.vector_store = (
                await self.blob_index_store.load()
            )

        # -----------------------------------------------------
        # If no existing index exists,
        # create a new one.
        # -----------------------------------------------------

        if self.vector_store is None:

            return await self.build_index()

        # -----------------------------------------------------
        # Download uploaded document
        # -----------------------------------------------------

        temp_path = None

        try:

            temp_path = (
                await self._download_blob_to_temp_file(
                    pathname
                )
            )

            # -------------------------------------------------
            # Calculate SHA-256
            # -------------------------------------------------

            document_hash = (
                self._calculate_file_hash(
                    temp_path
                )
            )

            # -------------------------------------------------
            # Check whether this document already exists
            # -------------------------------------------------

            existing_chunks = [
                metadata
                for metadata in self.vector_store.metadata
                if metadata.get("document_path")
                == pathname
            ]

            # -------------------------------------------------
            # SAME HASH → SKIP
            # -------------------------------------------------

            if existing_chunks:

                existing_hashes = {
                    metadata.get(
                        "document_hash"
                    )
                    for metadata in existing_chunks
                }

                if document_hash in existing_hashes:

                    return {
                        "status": "unchanged",
                        "documents_added": 0,
                        "documents_updated": 0,
                        "chunks_added": 0,
                    }

                # -------------------------------------------------
                # CHANGED DOCUMENT
                # Remove old vectors first.
                # -------------------------------------------------

                removed_chunks = (
                    self.vector_store.remove_document(
                        pathname
                    )
                )

                print(
                    f"UPDATED DOCUMENT: {pathname}"
                )

                print(
                    f"REMOVED OLD CHUNKS: "
                    f"{removed_chunks}"
                )

                documents_updated = 1

            else:

                documents_updated = 0

            # -------------------------------------------------
            # Extract text
            # -------------------------------------------------

            document = load_document(
                str(temp_path)
            )

            cleaned_text = clean_text(
                document["text"]
            )

            if not cleaned_text:

                raise ValueError(
                    "Document contains no usable text."
                )

            # -------------------------------------------------
            # Chunk document
            # -------------------------------------------------

            chunks = chunk_text_with_metadata(
                cleaned_text
            )

            if not chunks:

                raise ValueError(
                    "Document produced no chunks."
                )

            source_name = Path(
                pathname
            ).name

            metadata = []

            for chunk_index, chunk in enumerate(
                chunks
            ):

                metadata.append(
                    {
                        "source": source_name,
                        "document_path": pathname,
                        "document_hash": document_hash,
                        "section": chunk["section"],
                        "document_type": (
                            extension.lstrip(".")
                        ),
                        "chunk_id": (
                            f"{document_hash}"
                            f"_chunk_{chunk_index}"
                        ),
                        "text": chunk["text"],
                        "conversation_id": conversation_id,
                    }
                )

            # -------------------------------------------------
            # Generate embeddings ONLY for this document
            # -------------------------------------------------

            texts = [
                item["text"]
                for item in metadata
            ]

            embeddings = (
                self.embedding_service.embed_texts(
                    texts
                )
            )

            # -------------------------------------------------
            # Add new vectors
            # -------------------------------------------------

            self.vector_store.add_vectors(
                embeddings,
                metadata
            )

            # -------------------------------------------------
            # Persist updated index
            # -------------------------------------------------

            await self.blob_index_store.save(
                self.vector_store
            )

            if documents_updated:

                return {
                    "status": "updated",
                    "documents_added": 0,
                    "documents_updated": 1,
                    "chunks_added": len(metadata),
                }

            return {
                "status": "added",
                "documents_added": 1,
                "documents_updated": 0,
                "chunks_added": len(metadata),
            }

        finally:

            if (
                temp_path is not None
                and temp_path.exists()
            ):
                temp_path.unlink()

        # ---------------------------------------------------------
    # DELETE CONVERSATION DOCUMENTS
    # ---------------------------------------------------------

    async def delete_conversation_documents(
        self,
        conversation_id: int
    ) -> dict:

        # -----------------------------------------------------
        # Make sure vector store is available
        # -----------------------------------------------------

        if self.vector_store is None:

            self.vector_store = (
                await self.blob_index_store.load()
            )

        # -----------------------------------------------------
        # Find all documents belonging to conversation
        # -----------------------------------------------------

        prefix = f"documents/{conversation_id}/"

        blobs = await self.blob_service.list_files(
            prefix=prefix
        )

        deleted_documents = []

        for blob in blobs.blobs:

            pathname = blob.pathname

            extension = (
                Path(pathname)
                .suffix
                .lower()
            )

            if extension not in self.supported_extensions:
                continue

            # -------------------------------------------------
            # Delete document from Blob Storage
            # -------------------------------------------------

            await self.blob_service.delete_file(
                pathname
            )

            deleted_documents.append(
                pathname
            )

        # -----------------------------------------------------
        # Remove document vectors from FAISS
        # -----------------------------------------------------

        removed_chunks = 0

        if self.vector_store is not None:

            document_paths = {
                metadata.get("document_path")
                for metadata in self.vector_store.metadata
                if metadata.get("conversation_id")
                == conversation_id
            }

            for document_path in document_paths:

                if not document_path:
                    continue

                removed_chunks += (
                    self.vector_store.remove_document(
                        document_path
                    )
                )

            # -------------------------------------------------
            # Save updated FAISS index
            # -------------------------------------------------

            if removed_chunks > 0:

                await self.blob_index_store.save(
                    self.vector_store
                )

        return {
            "documents_deleted": len(
                deleted_documents
            ),
            "chunks_removed": removed_chunks
        }

    # ---------------------------------------------------------
    # LOAD PERSISTED INDEX
    # ---------------------------------------------------------

    async def load_persisted_index(self):

        vector_store = (
            await self.blob_index_store.load()
        )

        if vector_store is None:
            return None

        self.vector_store = vector_store

        return vector_store

    # ---------------------------------------------------------
    # INDEX STATUS
    # ---------------------------------------------------------

    async def get_index_status(self) -> dict:

        try:

            metadata = (
                await self.blob_index_store.get_metadata()
            )

            if metadata is None:

                return {
                    "indexed": False,
                    "documents": 0,
                    "chunks": 0,
                }

            unique_documents = {
                (
                    item.get("document_path")
                    or item.get("source")
                )
                for item in metadata
                if (
                    item.get("document_path")
                    or item.get("source")
                )
            }

            return {
                "indexed": True,
                "documents": len(
                    unique_documents
                ),
                "chunks": len(metadata),
            }

        except Exception as exc:

            print(
                f"INDEX STATUS ERROR: {exc}"
            )

            return {
                "indexed": False,
                "documents": 0,
                "chunks": 0,
            }