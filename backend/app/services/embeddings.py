import logging
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError


load_dotenv()

logger = logging.getLogger(__name__)


class EmbeddingService:

    def __init__(
        self,
        model: str = "gemini-embedding-2"
    ):
        self.model = model

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured in the environment."
            )

        self.client = genai.Client(
            api_key=api_key
        )

    # ---------------------------------------------------------
    # Query Embedding
    # ---------------------------------------------------------

    def embed_text(
        self,
        text: str
    ) -> list[float]:

        if not text or not text.strip():
            raise ValueError(
                "Text cannot be empty."
            )

        try:
            # Gemini Embedding 2 uses task instructions
            # directly in the input text.
            query_text = (
                f"task: question answering | query: {text}"
            )

            content = types.Content(
                parts=[
                    types.Part.from_text(
                        text=query_text
                    )
                ]
            )

            response = self.client.models.embed_content(
                model=self.model,
                contents=[content],
                config=types.EmbedContentConfig(
                    output_dimensionality=768
                )
            )

            return response.embeddings[0].values

        except APIError as exc:
            logger.exception(
                "Gemini query embedding API request failed."
            )

            raise RuntimeError(
                "Failed to generate query embedding "
                "due to a Gemini API error."
            ) from exc

        except Exception as exc:
            logger.exception(
                "Failed to generate query embedding."
            )

            raise RuntimeError(
                "Query embedding generation failed."
            ) from exc

    # ---------------------------------------------------------
    # Document Embeddings
    # ---------------------------------------------------------

    def embed_texts(
        self,
        texts: list[str]
    ) -> list[list[float]]:

        if not texts:
            raise ValueError(
                "Texts list cannot be empty."
            )

        try:
            contents = []

            for text in texts:

                if not text or not text.strip():
                    continue

                # Document representation for retrieval.
                document_text = (
                    f"title: none | text: {text}"
                )

                content = types.Content(
                    parts=[
                        types.Part.from_text(
                            text=document_text
                        )
                    ]
                )

                contents.append(content)

            if not contents:
                raise ValueError(
                    "No valid texts were provided."
                )

            # Gemini allows a maximum of 100 requests
            # in a single embedding batch.
            batch_size = 50

            embeddings = []

            for start in range(
                0,
                len(contents),
                batch_size
            ):
                batch = contents[
                    start:start + batch_size
                ]

                logger.info(
                    "Generating embeddings for batch "
                    "%d-%d of %d",
                    start + 1,
                    min(
                        start + batch_size,
                        len(contents)
                    ),
                    len(contents)
                )

                response = self.client.models.embed_content(
                    model=self.model,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        output_dimensionality=768
                    )
                )

                batch_embeddings = [
                    embedding.values
                    for embedding in response.embeddings
                ]

                if len(batch_embeddings) != len(batch):
                    raise RuntimeError(
                        "Gemini returned an unexpected number "
                        "of embeddings."
                    )

                embeddings.extend(batch_embeddings)

            return embeddings

        except APIError as exc:
            logger.exception(
                "Gemini batch embedding API request failed."
            )

            raise RuntimeError(
                "Failed to generate embeddings "
                "due to a Gemini API error."
            ) from exc

        except ValueError:
            raise

        except Exception as exc:
            logger.exception(
                "Failed to generate batch embeddings."
            )

            raise RuntimeError(
                "Batch embedding generation failed."
            ) from exc