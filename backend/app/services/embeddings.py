import ollama


class EmbeddingService:

    def __init__(self, model: str = "nomic-embed-text"):
        self.model = model

    def embed_text(self, text: str) -> list[float]:
        """
        Convert a single piece of text into an embedding vector.
        """

        response = ollama.embed(
            model=self.model,
            input=text
        )

        return response["embeddings"][0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Convert multiple texts into embedding vectors.
        """

        response = ollama.embed(
            model=self.model,
            input=texts
        )

        return response["embeddings"]