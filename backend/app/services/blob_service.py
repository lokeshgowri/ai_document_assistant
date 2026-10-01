import os
from dataclasses import dataclass

from vercel.blob import AsyncBlobClient


@dataclass
class BlobFileResult:
    content: bytes


class BlobStorageService:

    def __init__(self):
        token = os.getenv("BLOB_READ_WRITE_TOKEN")

        if not token:
            raise RuntimeError(
                "BLOB_READ_WRITE_TOKEN is not configured."
            )

        self.client = AsyncBlobClient(
            token=token
        )

    async def upload_file(
        self,
        pathname: str,
        data: bytes,
        content_type: str | None = None,
        overwrite: bool = False
    ):
        return await self.client.put(
            pathname,
            data,
            access="private",
            content_type=content_type,
            add_random_suffix=not overwrite,
            overwrite=overwrite
        )

    async def get_file(
        self,
        pathname: str
    ):
        result = await self.client.get(
            pathname,
            access="private"
        )

        if result is None:
            return None

        content = bytearray()

        async for chunk in result.stream:
            content.extend(chunk)

        return BlobFileResult(
            content=bytes(content)
        )

    async def list_files(
        self,
        prefix: str | None = None
    ):
        return await self.client.list_objects(
            prefix=prefix
        )

    async def delete_file(
        self,
        pathname: str
    ):
        await self.client.delete(
            pathname
        )