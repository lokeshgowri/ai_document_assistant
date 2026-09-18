from app.services.memory_extractor import MemoryExtractor
from app.services.memory_service import MemoryService


class MemoryManager:

    def __init__(self, db):
        self.memory_service = MemoryService(db)
        self.memory_extractor = MemoryExtractor()

    def process_user_message(self, user_message: str) -> list[dict]:

        memories = self.memory_extractor.extract(
            user_message
        )

        saved_memories = []

        for memory in memories:

            saved_memory = self.memory_service.save_or_update_memory(
                memory=memory["memory"],
                memory_type=memory["type"],
                importance=memory["importance"]
            )

            saved_memories.append({
                "id": saved_memory.id,
                "memory": saved_memory.memory,
                "type": saved_memory.memory_type,
                "importance": saved_memory.importance
            })

        return saved_memories

    def get_relevant_memories(
             self,
             limit: int = 10
             ) -> list[dict]:

         memories = self.memory_service.get_memories(
             limit=limit
             )
         return [
              {
                  "memory": memory.memory,
                  "type": memory.memory_type,
                  "importance": memory.importance
            }
            for memory in memories
            ]