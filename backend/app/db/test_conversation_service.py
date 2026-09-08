from app.db.database import Base, SessionLocal, engine
from app.services.conversation_service import ConversationService


def test_conversation_service():

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:

        service = ConversationService(db)

        # Create conversation
        conversation = service.create_conversation(
            "Test Conversation"
        )

        print(
            "Created:",
            conversation.id,
            conversation.title
        )

        # Add user message
        user_message = service.add_message(
            conversation_id=conversation.id,
            role="user",
            content="Hello"
        )

        print(
            "User message:",
            user_message.id,
            user_message.content
        )

        # Add assistant message
        assistant_message = service.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content="Hello! How can I help you?"
        )

        print(
            "Assistant message:",
            assistant_message.id,
            assistant_message.content
        )

        # Get conversation
        fetched = service.get_conversation(
            conversation.id
        )

        print(
            "Fetched conversation:",
            fetched.title
        )

        # Get messages
        messages = service.get_messages(
            conversation.id
        )

        print(
            "Message count:",
            len(messages)
        )

        # Soft delete
        deleted = service.soft_delete_conversation(
            conversation.id
        )

        print(
            "Soft deleted:",
            deleted
        )

        # Verify deleted conversation is hidden
        hidden = service.get_conversation(
            conversation.id
        )

        print(
            "Visible after soft delete:",
            hidden
        )

    finally:

        db.close()


if __name__ == "__main__":
    test_conversation_service()