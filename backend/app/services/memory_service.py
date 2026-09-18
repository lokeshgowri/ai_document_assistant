from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Memory


class MemoryService:

    def __init__(self, db: Session):
        self.db = db

    def save_memory(
        self,
        memory: str,
        memory_type: str,
        importance: int = 3
    ) -> Memory:

        new_memory = Memory(
            memory=memory,
            memory_type=memory_type,
            importance=importance,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        self.db.add(new_memory)
        self.db.commit()
        self.db.refresh(new_memory)

        return new_memory
    def save_or_update_memory(
            self,
            memory: str,
            memory_type: str,
            importance: int = 3
            ) -> Memory:
        normalized_memory = memory.strip().lower()
        existing_memories = self.db.query(Memory).all()
        for existing_memory in existing_memories:
            if (
                existing_memory.memory.strip().lower()
                == normalized_memory
                and existing_memory.memory_type == memory_type
                ):
                existing_memory.importance = importance
                existing_memory.updated_at = datetime.now(timezone.utc)
                self.db.commit()
                self.db.refresh(existing_memory)
                return existing_memory
            return self.save_memory(
                memory=memory,
                memory_type=memory_type,
                importance=importance
                )

    def get_memories(
        self,
        limit: int = 20
    ) -> list[Memory]:

        statement = (
            select(Memory)
            .order_by(
                Memory.importance.desc(),
                Memory.updated_at.desc()
            )
            .limit(limit)
        )

        result = self.db.execute(statement)

        return list(result.scalars().all())

    def update_memory(
        self,
        memory_id: int,
        memory: str | None = None,
        memory_type: str | None = None,
        importance: int | None = None
    ) -> Memory | None:

        existing_memory = self.db.get(Memory, memory_id)

        if existing_memory is None:
            return None

        if memory is not None:
            existing_memory.memory = memory

        if memory_type is not None:
            existing_memory.memory_type = memory_type

        if importance is not None:
            existing_memory.importance = importance

        existing_memory.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(existing_memory)

        return existing_memory

    def delete_memory(self, memory_id: int) -> bool:

        existing_memory = self.db.get(Memory, memory_id)

        if existing_memory is None:
            return False

        self.db.delete(existing_memory)
        self.db.commit()

        return True