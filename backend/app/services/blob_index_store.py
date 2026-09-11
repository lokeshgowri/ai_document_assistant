import json
import tempfile
from pathlib import Path

import faiss

from app.config import (
    EMBEDDING_PROVIDER,
    EMBEDDING_MODEL,
    OLLAMA_EMBEDDING_MODEL,
)

from app.services.blob_service import BlobStorageService
from app.services.vector_store import VectorStore


class BlobIndexStore:

    INDEX_PATHNAME = "index/index.faiss"
    METADATA_PATHNAME = "index/metadata.json"
    CONFIG_PATHNAME = "index/config.json"

    def __init__(self):
        self.blob_service = BlobStorageService()

    # ======================================================
    # SAVE INDEX
    # ======================================================

    async def save(self, vector_store: VectorStore):

        temp_index_path = None

        try:

            # --------------------------------------------------
            # Create temporary FAISS file
            # --------------------------------------------------

            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".faiss"
            )

            temp_index_path = Path(temp_file.name)
            temp_file.close()

            # --------------------------------------------------
            # Write FAISS index
            # --------------------------------------------------

            faiss.write_index(
                vector_store.index,
                str(temp_index_path)
            )

            index_bytes = temp_index_path.read_bytes()

            # --------------------------------------------------
            # Upload FAISS index
            # --------------------------------------------------

            await self.blob_service.upload_file(
                pathname=self.INDEX_PATHNAME,
                data=index_bytes,
                content_type="application/octet-stream",
                overwrite=True
            )

            # --------------------------------------------------
            # Save metadata + FAISS ID mapping
            # --------------------------------------------------

            metadata_store = {
                "metadata": vector_store.metadata,
                "id_to_metadata_index": {
                    str(vector_id): metadata_index
                    for vector_id, metadata_index
                    in vector_store.id_to_metadata_index.items()
                },
                "next_vector_id": vector_store.next_vector_id
            }

            metadata_bytes = json.dumps(
                metadata_store,
                ensure_ascii=False,
                indent=2
            ).encode("utf-8")

            await self.blob_service.upload_file(
                pathname=self.METADATA_PATHNAME,
                data=metadata_bytes,
                content_type="application/json",
                overwrite=True
            )

            # --------------------------------------------------
            # Save embedding configuration
            # --------------------------------------------------

            embedding_model = EMBEDDING_MODEL

            if EMBEDDING_PROVIDER == "ollama":
                embedding_model = OLLAMA_EMBEDDING_MODEL

            index_config = {
                "embedding_provider": EMBEDDING_PROVIDER,
                "embedding_model": embedding_model,
                "embedding_dimension": vector_store.index.d
            }

            config_bytes = json.dumps(
                index_config,
                ensure_ascii=False,
                indent=2
            ).encode("utf-8")

            await self.blob_service.upload_file(
                pathname=self.CONFIG_PATHNAME,
                data=config_bytes,
                content_type="application/json",
                overwrite=True
            )

        finally:

            if (
                temp_index_path is not None
                and temp_index_path.exists()
            ):
                temp_index_path.unlink()

    # ======================================================
    # LOAD INDEX
    # ======================================================

    async def load(self):

        index_temp_path = None

        try:

            # --------------------------------------------------
            # Load FAISS index
            # --------------------------------------------------

            index_result = await self.blob_service.get_file(
                self.INDEX_PATHNAME
            )

            if index_result is None:
                return None

            index_bytes = index_result.content

            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".faiss"
            )

            index_temp_path = Path(temp_file.name)

            try:
                temp_file.write(index_bytes)
            finally:
                temp_file.close()

            faiss_index = faiss.read_index(
                str(index_temp_path)
            )

            # --------------------------------------------------
            # Load metadata
            # --------------------------------------------------

            metadata_result = await self.blob_service.get_file(
                self.METADATA_PATHNAME
            )

            if metadata_result is None:
                return None

            metadata_bytes = metadata_result.content

            metadata_data = json.loads(
                metadata_bytes.decode("utf-8")
            )

            # --------------------------------------------------
            # Support both new and old metadata formats
            # --------------------------------------------------

            if isinstance(metadata_data, dict):

                metadata = metadata_data.get(
                    "metadata",
                    []
                )

                id_to_metadata_index = {
                    int(vector_id): metadata_index
                    for vector_id, metadata_index
                    in metadata_data.get(
                        "id_to_metadata_index",
                        {}
                    ).items()
                }

                next_vector_id = metadata_data.get(
                    "next_vector_id",
                    0
                )

            else:

                # Legacy format:
                # metadata was stored directly as a list

                metadata = metadata_data

                id_to_metadata_index = {}

                next_vector_id = 0

            # --------------------------------------------------
            # Load embedding configuration
            # --------------------------------------------------

            config_result = await self.blob_service.get_file(
                self.CONFIG_PATHNAME
            )

            if config_result is None:

                raise RuntimeError(
                    "Embedding configuration for the "
                    "FAISS index was not found."
                )

            config_bytes = config_result.content

            index_config = json.loads(
                config_bytes.decode("utf-8")
            )

            # --------------------------------------------------
            # Validate embedding configuration
            # --------------------------------------------------

            current_provider = EMBEDDING_PROVIDER

            current_model = EMBEDDING_MODEL

            if current_provider == "ollama":
                current_model = OLLAMA_EMBEDDING_MODEL

            stored_provider = index_config.get(
                "embedding_provider"
            )

            stored_model = index_config.get(
                "embedding_model"
            )

            stored_dimension = index_config.get(
                "embedding_dimension"
            )

            if stored_provider != current_provider:

                raise RuntimeError(
                    "Embedding provider mismatch. "
                    f"Existing index uses "
                    f"'{stored_provider}', but the current "
                    f"configuration uses "
                    f"'{current_provider}'."
                )

            if stored_model != current_model:

                raise RuntimeError(
                    "Embedding model mismatch. "
                    f"Existing index uses "
                    f"'{stored_model}', but the current "
                    f"configuration uses "
                    f"'{current_model}'."
                )

            if stored_dimension != faiss_index.d:

                raise RuntimeError(
                    "Embedding dimension mismatch. "
                    f"Index configuration specifies "
                    f"{stored_dimension}, but the FAISS "
                    f"index has dimension "
                    f"{faiss_index.d}."
                )

            # --------------------------------------------------
            # Reconstruct VectorStore
            # --------------------------------------------------

            vector_store = VectorStore(
                dimension=faiss_index.d
            )

            vector_store.index = faiss_index

            vector_store.metadata = metadata

            vector_store.id_to_metadata_index = (
                id_to_metadata_index
            )

            # --------------------------------------------------
            # Recover next vector ID
            # --------------------------------------------------

            if next_vector_id:

                vector_store.next_vector_id = next_vector_id

            elif id_to_metadata_index:

                vector_store.next_vector_id = (
                    max(id_to_metadata_index.keys()) + 1
                )

            else:

                vector_store.next_vector_id = 0

            return vector_store

        except Exception as exc:

            if "does not exist" in str(exc).lower():
                return None

            raise

        finally:

            if (
                index_temp_path is not None
                and index_temp_path.exists()
            ):
                index_temp_path.unlink()

    # ======================================================
    # GET METADATA
    # ======================================================

    async def get_metadata(self):

        result = await self.blob_service.get_file(
            self.METADATA_PATHNAME
        )

        if result is None:
            return None

        metadata_bytes = result.content

        metadata_data = json.loads(
            metadata_bytes.decode("utf-8")
        )

        # New format
        if isinstance(metadata_data, dict):

            return metadata_data.get(
                "metadata",
                []
            )

        # Legacy format
        return metadata_data

    # ======================================================
    # GET INDEX CONFIGURATION
    # ======================================================

    async def get_index_config(self):

        result = await self.blob_service.get_file(
            self.CONFIG_PATHNAME
        )

        if result is None:
            return None

        config_bytes = result.content

        return json.loads(
            config_bytes.decode("utf-8")
        )