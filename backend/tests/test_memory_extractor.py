from app.services.memory_extractor import MemoryExtractor


def test_memory_extractor():

    extractor = MemoryExtractor()

    test_messages = [
        "I work in the Finance department.",
        "I prefer short answers.",
        "I'm preparing for a Python Full Stack Developer interview.",
        "Remember that I use FastAPI.",
        "What is FastAPI?",
        "Can someone from Finance access this document?"
    ]

    for message in test_messages:

        print("\n===================================")
        print("USER:", message)

        memories = extractor.extract(message)

        print("EXTRACTED MEMORIES:")

        for memory in memories:
            print(memory)

        print("===================================")