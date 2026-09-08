import os

from vercel.blob import AsyncBlobClient


class BlobStorageService:

    def __init__(self):

        token = os.getenv(
            "BLOB_READ_WRITE_TOKEN"
        )

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

        return await self.client.get(
            pathname,
            access="private"
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