from app.db.database import SessionLocal
from app.services.memory_service import MemoryService


def test_memory_service():

    db = SessionLocal()

    try:
        memory_service = MemoryService(db)

        # 1. SAVE
        memory = memory_service.save_memory(
            memory="User is preparing for a Python Full Stack interview.",
            memory_type="goal",
            importance=5
        )

        print("\nSaved memory:")
        print(memory.id)
        print(memory.memory)
        print(memory.memory_type)
        print(memory.importance)

        # 2. GET
        memories = memory_service.get_memories()

        print("\nAll memories:")

        for item in memories:
            print(
                item.id,
                "|",
                item.memory,
                "|",
                item.memory_type,
                "|",
                item.importance
            )

        # 3. UPDATE
        updated_memory = memory_service.update_memory(
            memory_id=memory.id,
            memory="User is preparing for a Python Full Stack Developer interview.",
            importance=5
        )

        print("\nUpdated memory:")
        print(updated_memory.memory)
        print(updated_memory.importance)

        # 4. DELETE
        deleted = memory_service.delete_memory(memory.id)

        print("\nMemory deleted:", deleted)

        # 5. VERIFY DELETE
        memories_after_delete = memory_service.get_memories()

        print("\nMemories after deletion:")

        for item in memories_after_delete:
            print(item.id, "|", item.memory)

    finally:
        db.close()