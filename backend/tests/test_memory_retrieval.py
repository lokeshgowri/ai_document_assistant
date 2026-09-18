from app.db.database import SessionLocal
from app.services.memory_manager import MemoryManager


def test_memory_retrieval():

    db = SessionLocal()

    try:
        manager = MemoryManager(db)

        memories = manager.get_relevant_memories(
            limit=10
        )

        print("\nRetrieved memories:")

        for memory in memories:
            print(memory)

    finally:
        db.close()