import asyncio
from pathlib import Path

from dotenv import load_dotenv

from app.services.blob_service import BlobStorageService


load_dotenv()


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt"
}


async def main():

    data_directory = Path("data")

    blob_service = BlobStorageService()

    files = [
        file
        for file in data_directory.iterdir()
        if file.is_file()
        and file.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    print(
        f"Found {len(files)} documents in data/"
    )

    if not files:

        print(
            "No supported documents found."
        )

        return

    print()

    for file_path in files:

        print(
            f"Uploading: {file_path.name}"
        )

        file_bytes = (
            file_path.read_bytes()
        )

        content_type = {
            ".pdf": "application/pdf",
            ".docx": (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            ".txt": "text/plain"
        }.get(
            file_path.suffix.lower(),
            "application/octet-stream"
        )

        pathname = (
            f"documents/{file_path.name}"
        )

        blob = await blob_service.upload_file(
            pathname=pathname,
            data=file_bytes,
            content_type=content_type,
            overwrite=True
        )

        print(
            f"  Uploaded successfully: "
            f"{blob.pathname}"
        )

    print()
    print(
        "All documents uploaded successfully."
    )


if __name__ == "__main__":

    asyncio.run(main())