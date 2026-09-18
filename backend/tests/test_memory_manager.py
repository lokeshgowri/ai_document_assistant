from app.db.database import SessionLocal
from app.services.memory_manager import MemoryManager


def test_memory_manager():

    db = SessionLocal()

    try:
        manager = MemoryManager(db)

        messages = [
            "I work in the Finance department.",
            "I prefer short answers.",
            "I'm preparing for a Python Full Stack Developer interview.",
            "What is FastAPI?"
        ]

        for message in messages:

            print("\n================================")
            print("USER:", message)

            saved_memories = manager.process_user_message(
                message
            )

            print("SAVED MEMORIES:")

            for memory in saved_memories:
                print(memory)

            print("================================")

    finally:
        db.close()