import json
import os
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import Conversation, Message
from app.services.blob_service import BlobStorageService


class ConversationService:

    def __init__(self, db: Session | None = None):
        self.db = db
        self.use_blob = os.getenv("VERCEL") == "1"

        if self.use_blob:
            self.blob_service = BlobStorageService()

    # =========================================================
    # BLOB HELPERS
    # =========================================================

    def _blob_path(self, conversation_id: int) -> str:
        return f"conversations/{conversation_id}.json"

    async def _get_blob_conversation(
        self,
        conversation_id: int
    ):
        result = await self.blob_service.get_file(
            self._blob_path(conversation_id)
        )

        if result is None:
            return None

        return json.loads(
            result.content.decode("utf-8")
        )

    async def _save_blob_conversation(
        self,
        conversation: dict
    ):
        data = json.dumps(
            conversation,
            ensure_ascii=False,
            indent=2
        ).encode("utf-8")

        await self.blob_service.upload_file(
            pathname=self._blob_path(
                conversation["id"]
            ),
            data=data,
            content_type="application/json",
            overwrite=True
        )

    async def _next_blob_id(self) -> int:
        result = await self.blob_service.list_files(
            prefix="conversations/"
        )

        max_id = 0

        for blob in result.blobs:
            pathname = blob.pathname

            if not pathname.endswith(".json"):
                continue

            try:
                conversation_id = int(
                    pathname
                    .split("/")[-1]
                    .replace(".json", "")
                )

                max_id = max(
                    max_id,
                    conversation_id
                )

            except ValueError:
                continue

        return max_id + 1

    # =========================================================
    # CREATE CONVERSATION
    # =========================================================

    async def create_conversation(
        self,
        title: str = "New Conversation"
    ):

        if self.use_blob:

            conversation_id = (
                await self._next_blob_id()
            )

            now = datetime.now(
                timezone.utc
            ).isoformat()

            conversation = {
                "id": conversation_id,
                "title": title,
                "created_at": now,
                "updated_at": now,
                "deleted_at": None,
                "messages": []
            }

            await self._save_blob_conversation(
                conversation
            )

            return conversation

        conversation = Conversation(
            title=title
        )

        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        return conversation

    # =========================================================
    # GET ACTIVE CONVERSATIONS
    # =========================================================

    async def get_conversations(self):

        if self.use_blob:

            result = await self.blob_service.list_files(
                prefix="conversations/"
            )

            conversations = []

            for blob in result.blobs:

                if not blob.pathname.endswith(".json"):
                    continue

                try:
                    conversation = (
                        await self._get_blob_conversation(
                            int(
                                blob.pathname
                                .split("/")[-1]
                                .replace(".json", "")
                            )
                        )
                    )

                    if conversation is None:
                        continue

                    if conversation.get(
                        "deleted_at"
                    ) is None:

                        conversations.append(
                            conversation
                        )

                except Exception:
                    continue

            conversations.sort(
                key=lambda item: item.get(
                    "updated_at",
                    ""
                ),
                reverse=True
            )

            return conversations

        return (
            self.db.query(Conversation)
            .filter(
                Conversation.deleted_at.is_(None)
            )
            .order_by(
                Conversation.updated_at.desc()
            )
            .all()
        )
    # =========================================================
    # UPDATE CONVERSATION TITLE
    # =========================================================

    async def update_title(
        self,
        conversation_id: int,
        title: str
    ):

        if self.use_blob:

            conversation = (
                await self._get_blob_conversation(
                    conversation_id
                )
            )

            if conversation is None:
                return None

            conversation["title"] = title

            conversation["updated_at"] = (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )

            await self._save_blob_conversation(
                conversation
            )

            return conversation

        conversation = (
            self.db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.deleted_at.is_(None)
            )
            .first()
        )

        if not conversation:
            return None

        conversation.title = title

        conversation.updated_at = (
            datetime.now(timezone.utc)
        )

        self.db.commit()
        self.db.refresh(conversation)

        return conversation

    # =========================================================
    # GET ONE CONVERSATION
    # =========================================================

    async def get_conversation(
        self,
        conversation_id: int
    ):

        if self.use_blob:

            conversation = (
                await self._get_blob_conversation(
                    conversation_id
                )
            )

            if not conversation:
                return None

            if conversation.get(
                "deleted_at"
            ) is not None:
                return None

            return conversation

        return (
            self.db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.deleted_at.is_(None)
            )
            .first()
        )

    # =========================================================
    # ADD MESSAGE
    # =========================================================

    async def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str
    ):

        if self.use_blob:

            conversation = (
                await self._get_blob_conversation(
                    conversation_id
                )
            )

            if conversation is None:
                return None

            messages = conversation.setdefault(
                "messages",
                []
            )

            next_message_id = 1

            if messages:
                next_message_id = (
                    max(
                        message.get("id", 0)
                        for message in messages
                    )
                    + 1
                )

            message = {
                "id": next_message_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "created_at": (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                )
            }

            messages.append(message)

            conversation["updated_at"] = (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )

            await self._save_blob_conversation(
                conversation
            )

            return message

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )

        self.db.add(message)

        conversation = (
            self.db.query(Conversation)
            .filter(
                Conversation.id == conversation_id
            )
            .first()
        )

        if conversation:
            conversation.updated_at = (
                datetime.now(timezone.utc)
            )

        self.db.commit()
        self.db.refresh(message)

        return message

    # =========================================================
    # GET MESSAGES
    # =========================================================

    async def get_messages(
        self,
        conversation_id: int
    ):

        if self.use_blob:

            conversation = (
                await self._get_blob_conversation(
                    conversation_id
                )
            )

            if not conversation:
                return []

            return conversation.get(
                "messages",
                []
            )

        return (
            self.db.query(Message)
            .filter(
                Message.conversation_id == conversation_id
            )
            .order_by(
                Message.created_at.asc()
            )
            .all()
        )

    # =========================================================
    # SOFT DELETE CONVERSATION
    # =========================================================

    async def soft_delete_conversation(
        self,
        conversation_id: int
    ) -> bool:

        if self.use_blob:

            conversation = (
                await self._get_blob_conversation(
                    conversation_id
                )
            )

            if (
                conversation is None
                or conversation.get("deleted_at")
                is not None
            ):
                return False

            conversation["deleted_at"] = (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )

            conversation["updated_at"] = (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )

            await self._save_blob_conversation(
                conversation
            )

            return True

        conversation = (
            self.db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.deleted_at.is_(None)
            )
            .first()
        )

        if not conversation:
            return False

        conversation.deleted_at = (
            datetime.now(timezone.utc)
        )

        self.db.commit()

        return True

    # =========================================================
    # PERMANENT DELETE
    # =========================================================

    async def permanently_delete_conversation(
        self,
        conversation_id: int
    ) -> bool:

        if self.use_blob:

            conversation = (
                await self._get_blob_conversation(
                    conversation_id
                )
            )

            if conversation is None:
                return False

            await self.blob_service.delete_file(
                self._blob_path(
                    conversation_id
                )
            )

            return True

        conversation = (
            self.db.query(Conversation)
            .filter(
                Conversation.id == conversation_id
            )
            .first()
        )

        if not conversation:
            return False

        self.db.delete(conversation)

        self.db.commit()

        return True