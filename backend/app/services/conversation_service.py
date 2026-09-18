import json
import os
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models import Conversation, Message
from app.services.blob_service import BlobStorageService
from vercel._internal.blob.errors import BlobNotFoundError


class ConversationService:

    def __init__(self, db: Session | None = None):
        self.db = db

        # Local development -> SQLite
        # Vercel production -> Vercel Blob
        self.use_blob = os.getenv("VERCEL") == "1"

        if self.use_blob:
            self.blob_service = BlobStorageService()

    # =========================================================
    # BLOB PATH HELPERS
    # =========================================================

    def _blob_path(self, conversation_id: int) -> str:
        return f"conversations/{conversation_id}.json"

    def _message_blob_path(
        self,
        conversation_id: int,
        message_id: str
    ) -> str:
        return (
            f"conversation-messages/"
            f"{conversation_id}/"
            f"{message_id}.json"
        )

    # =========================================================
    # BLOB CONVERSATION HELPERS
    # =========================================================

    async def _get_blob_conversation(
        self,
        conversation_id: int
    ):
        try:
            result = await self.blob_service.get_file(
                self._blob_path(conversation_id)
            )
        except BlobNotFoundError:
            return None

        if result is None:
            return None

        return json.loads(
            result.content.decode("utf-8")
        )

    async def _save_blob_conversation(
        self,
        conversation: dict
    ):
        """
        Save only conversation metadata.

        Messages are stored separately so concurrent
        Vercel requests cannot overwrite each other's messages.
        """

        conversation_data = {
            "id": conversation["id"],
            "title": conversation.get(
                "title",
                "New Conversation"
            ),
            "created_at": conversation["created_at"],
            "updated_at": conversation["updated_at"],
            "deleted_at": conversation.get("deleted_at")
        }

        data = json.dumps(
            conversation_data,
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

    # =========================================================
    # MESSAGE BLOB HELPERS
    # =========================================================

    async def _save_blob_message(
        self,
        message: dict
    ):
        data = json.dumps(
            message,
            ensure_ascii=False,
            indent=2
        ).encode("utf-8")

        await self.blob_service.upload_file(
            pathname=self._message_blob_path(
                message["conversation_id"],
                message["id"]
            ),
            data=data,
            content_type="application/json",
            overwrite=False
        )

    async def _get_blob_messages(
        self,
        conversation_id: int
    ) -> list[dict]:

        prefix = (
            f"conversation-messages/"
            f"{conversation_id}/"
        )

        result = await self.blob_service.list_files(
            prefix=prefix
        )

        messages = []

        for blob in result.blobs:

            pathname = blob.pathname

            if not pathname.endswith(".json"):
                continue

            try:
                message_id = (
                    pathname
                    .split("/")[-1]
                    .replace(".json", "")
                )

                blob_result = (
                    await self.blob_service.get_file(
                        pathname
                    )
                )

                if blob_result is None:
                    continue

                message = json.loads(
                    blob_result.content.decode("utf-8")
                )

                # Make sure the message belongs to this
                # conversation.
                if (
                    message.get("conversation_id")
                    != conversation_id
                ):
                    continue

                # Preserve the original message ID.
                if not message.get("id"):
                    message["id"] = message_id

                messages.append(message)

            except Exception:
                # Ignore malformed individual message blobs
                # rather than breaking the whole conversation.
                continue

        messages.sort(
            key=lambda message: message.get(
                "created_at",
                ""
            )
        )

        return messages

    async def _delete_blob_messages(
        self,
        conversation_id: int
    ) -> int:

        prefix = (
            f"conversation-messages/"
            f"{conversation_id}/"
        )

        result = await self.blob_service.list_files(
            prefix=prefix
        )

        deleted = 0

        for blob in result.blobs:

            pathname = blob.pathname

            if not pathname.endswith(".json"):
                continue

            try:
                await self.blob_service.delete_file(
                    pathname
                )
                deleted += 1
            except Exception:
                continue

        return deleted

    # =========================================================
    # LEGACY MESSAGE SUPPORT
    # =========================================================

    async def _get_messages_with_legacy_support(
        self,
        conversation: dict
    ) -> list[dict]:

        conversation_id = conversation["id"]

        # New production format
        messages = await self._get_blob_messages(
            conversation_id
        )

        if messages:
            return messages

        # Existing conversations created before this change
        legacy_messages = conversation.get(
            "messages",
            []
        )

        return legacy_messages

    # =========================================================
    # NEXT CONVERSATION ID
    # =========================================================

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
                "deleted_at": None
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

                    conversation_id = int(
                        blob.pathname
                        .split("/")[-1]
                        .replace(".json", "")
                    )

                    conversation = (
                        await self._get_blob_conversation(
                            conversation_id
                        )
                    )

                    if conversation is None:
                        continue

                    if conversation.get(
                        "deleted_at"
                    ) is not None:
                        continue

                    # Include messages for compatibility
                    conversation["messages"] = (
                        await self._get_messages_with_legacy_support(
                            conversation
                        )
                    )

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

            conversation["messages"] = (
                await self._get_messages_with_legacy_support(
                    conversation
                )
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

            conversation["messages"] = (
                await self._get_messages_with_legacy_support(
                    conversation
                )
            )

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

            if conversation.get(
                "deleted_at"
            ) is not None:
                return None

            # -------------------------------------------------
            # IMPORTANT:
            # Each message gets its own unique Blob.
            # No read-modify-write of the conversation occurs.
            # -------------------------------------------------

            message_id = uuid4().hex

            now = datetime.now(
                timezone.utc
            ).isoformat()

            message = {
                "id": message_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "created_at": now
            }

            await self._save_blob_message(
                message
            )

            # Only update conversation metadata.
            # We DO NOT touch a messages array.
            conversation["updated_at"] = now

            await self._save_blob_conversation(
                conversation
            )

            return message

        # -----------------------------------------------------
        # SQLITE
        # -----------------------------------------------------

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

            return (
                await self._get_messages_with_legacy_support(
                    conversation
                )
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

            now = datetime.now(
                timezone.utc
            ).isoformat()

            conversation["deleted_at"] = now
            conversation["updated_at"] = now

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

            # Delete all individual message blobs.
            await self._delete_blob_messages(
                conversation_id
            )

            # Delete the conversation metadata.
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