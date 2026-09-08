import json
import tempfile
from pathlib import Path

import faiss

from app.services.blob_service import BlobStorageService
from app.services.vector_store import VectorStore


class BlobIndexStore:

    INDEX_PATHNAME = "index/index.faiss"
    METADATA_PATHNAME = "index/metadata.json"

    def __init__(self):

        self.blob_service = BlobStorageService()

    async def save(
        self,
        vector_store: VectorStore
    ):

        temp_index_path = None

        try:

            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".faiss"
            )

            temp_index_path = Path(
                temp_file.name
            )

            temp_file.close()

            faiss.write_index(
                vector_store.index,
                str(temp_index_path)
            )

            index_bytes = (
                temp_index_path.read_bytes()
            )

            await self.blob_service.upload_file(
                pathname=self.INDEX_PATHNAME,
                data=index_bytes,
                content_type="application/octet-stream",
                overwrite=True
            )

            metadata_bytes = json.dumps(
                vector_store.metadata,
                ensure_ascii=False,
                indent=2
            ).encode("utf-8")

            await self.blob_service.upload_file(
                pathname=self.METADATA_PATHNAME,
                data=metadata_bytes,
                content_type="application/json",
                overwrite=True
            )

        finally:

            if (
                temp_index_path is not None
                and temp_index_path.exists()
            ):
                temp_index_path.unlink()

    async def load(self):

        index_temp_path = None

        try:

            index_result = (
                await self.blob_service.get_file(
                    self.INDEX_PATHNAME
                )
            )

            if index_result is None:
                return None

            index_bytes = index_result.content

            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".faiss"
            )

            index_temp_path = Path(
                temp_file.name
            )

            try:

                temp_file.write(
                    index_bytes
                )

            finally:

                temp_file.close()

            faiss_index = faiss.read_index(
                str(index_temp_path)
            )

            metadata_result = (
                await self.blob_service.get_file(
                    self.METADATA_PATHNAME
                )
            )

            if metadata_result is None:
                return None

            metadata_bytes = (
                metadata_result.content
            )

            metadata = json.loads(
                metadata_bytes.decode("utf-8")
            )

            vector_store = VectorStore(
                dimension=faiss_index.d
            )

            vector_store.index = faiss_index

            vector_store.metadata = metadata

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

    async def get_metadata(self):

        result = (
            await self.blob_service.get_file(
                self.METADATA_PATHNAME
            )
        )

        if result is None:
            return None

        metadata_bytes = result.content

        return json.loads(
            metadata_bytes.decode("utf-8")
        )