from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import Conversation, Message


class ConversationService:

    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------
    # CREATE CONVERSATION
    # ---------------------------------------------------------

    def create_conversation(
        self,
        title: str = "New Conversation"
    ) -> Conversation:

        conversation = Conversation(
            title=title
        )

        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        return conversation

    # ---------------------------------------------------------
    # GET ACTIVE CONVERSATIONS
    # ---------------------------------------------------------

    def get_conversations(self) -> list[Conversation]:

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

    # ---------------------------------------------------------
    # GET ONE ACTIVE CONVERSATION
    # ---------------------------------------------------------

    def get_conversation(
        self,
        conversation_id: int
    ) -> Conversation | None:

        return (
            self.db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.deleted_at.is_(None)
            )
            .first()
        )

    # ---------------------------------------------------------
    # ADD MESSAGE
    # ---------------------------------------------------------

    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str
    ) -> Message:

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
            conversation.updated_at = datetime.now(
                timezone.utc
            )

        self.db.commit()
        self.db.refresh(message)

        return message

    # ---------------------------------------------------------
    # GET MESSAGES
    # ---------------------------------------------------------

    def get_messages(
        self,
        conversation_id: int
    ) -> list[Message]:

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

    # ---------------------------------------------------------
    # SOFT DELETE CONVERSATION
    # ---------------------------------------------------------

    def soft_delete_conversation(
        self,
        conversation_id: int
    ) -> bool:

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

        conversation.deleted_at = datetime.now(
            timezone.utc
        )

        self.db.commit()

        return True

    # ---------------------------------------------------------
    # PERMANENT DELETE CONVERSATION
    # ---------------------------------------------------------

    def permanently_delete_conversation(
        self,
        conversation_id: int
    ) -> bool:

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