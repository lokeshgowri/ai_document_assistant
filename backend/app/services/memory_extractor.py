import json

from app.services.llm_service import LLMService


class MemoryExtractor:

    def __init__(self):
        self.llm_service = LLMService()

    def extract(self, user_message: str) -> list[dict]:

        if not user_message or not user_message.strip():
            return []

        prompt = f"""
You are a memory extraction system.

Your job is to identify information that the user explicitly states
about themselves and that could be useful in future conversations.

Only extract information that the user explicitly states or clearly confirms.

Possible memory types:
- profile
- preference
- goal
- explicit_memory

DO NOT remember:
- normal questions
- document facts
- RAG answers
- temporary conversation details
- greetings
- small talk
- hypothetical examples
- assumptions
- information inferred from the user's question

Examples:

User:
"I work in the Finance department."

Output:
[
  {{
    "memory": "User works in the Finance department.",
    "type": "profile",
    "importance": 5
  }}
]

User:
"I prefer short answers."

Output:
[
  {{
    "memory": "User prefers short answers.",
    "type": "preference",
    "importance": 3
  }}
]

User:
"I'm preparing for a Python Full Stack Developer interview."

Output:
[
  {{
    "memory": "User is preparing for a Python Full Stack Developer interview.",
    "type": "goal",
    "importance": 4
  }}
]

User:
"Remember that I use FastAPI."

Output:
[
  {{
    "memory": "User uses FastAPI.",
    "type": "explicit_memory",
    "importance": 5
  }}
]

User:
"What is FastAPI?"

Output:
[]

User:
"Can someone from Finance access this document?"

Output:
[]

Return ONLY valid JSON.
Do not include markdown.
Do not include explanations.

User message:
{user_message}
"""

        response = self.llm_service.generate_memory(prompt)        

        try:
            data = json.loads(response)

            if not isinstance(data, list):
                return []

            memories = []

            for item in data:
                if not isinstance(item, dict):
                    continue

                memory = item.get("memory")
                memory_type = item.get("type")
                importance = item.get("importance")

                if not memory or not memory_type:
                    continue

                if memory_type not in {
                    "profile",
                    "preference",
                    "goal",
                    "explicit_memory"
                }:
                    continue

                try:
                    importance = int(importance)
                except (TypeError, ValueError):
                    importance = 3

                importance = max(1, min(5, importance))

                memories.append({
                    "memory": memory.strip(),
                    "type": memory_type,
                    "importance": importance
                })

            return memories

        except (json.JSONDecodeError, TypeError):
            return []