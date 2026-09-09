import json
from datetime import datetime, timezone

from app.services.blob_service import BlobStorageService


class BlobConversationService:

    PREFIX = "conversations/"

    def __init__(self):
        self.blob_service = BlobStorageService()

    def _pathname(self, conversation_id: int) -> str:
        return f"{self.PREFIX}{conversation_id}.json"

    async def get_conversation(
        self,
        conversation_id: int
    ):
        result = await self.blob_service.get_file(
            self._pathname(conversation_id)
        )

        if result is None:
            return None

        return json.loads(
            result.content.decode("utf-8")
        )

    async def save_conversation(
        self,
        conversation: dict
    ):
        conversation["updated_at"] = (
            datetime.now(timezone.utc).isoformat()
        )

        data = json.dumps(
            conversation,
            ensure_ascii=False,
            indent=2
        ).encode("utf-8")

        await self.blob_service.upload_file(
            pathname=self._pathname(
                conversation["id"]
            ),
            data=data,
            content_type="application/json",
            overwrite=True
        )

        return conversation

    async def delete_conversation(
        self,
        conversation_id: int
    ):
        await self.blob_service.delete_file(
            self._pathname(conversation_id)
        )

    async def list_conversations(self):
        result = await self.blob_service.list_files(
            prefix=self.PREFIX
        )

        conversations = []

        for item in result.blobs:
            try:
                blob = await self.blob_service.get_file(
                    item.pathname
                )

                if blob is None:
                    continue

                conversation = json.loads(
                    blob.content.decode("utf-8")
                )

                conversations.append(
                    conversation
                )

            except Exception:
                continue

        conversations.sort(
            key=lambda x: x.get(
                "updated_at",
                ""
            ),
            reverse=True
        )

        return conversations