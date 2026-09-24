from dotenv import load_dotenv

load_dotenv()

import asyncio


from app.services.blob_service import BlobStorageService


async def main():
    blob_service = BlobStorageService()

    print("Testing Blob access...")
    print("Token exists:", bool(blob_service.client))

    try:
        result = await blob_service.get_file("index/index.faiss")

        if result is None:
            print("RESULT: Blob was not found.")
        else:
            print("RESULT: Blob downloaded successfully.")
            print("Size:", len(result.content), "bytes")

    except Exception as exc:
        print("RESULT: Blob download failed.")
        print("ERROR:", exc)


asyncio.run(main())