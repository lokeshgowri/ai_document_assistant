import os
import random
import re
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError


load_dotenv()


class EmbeddingService:

    def __init__(
        self,
        model: str = "gemini-embedding-2"
    ):

        self.model = model

        api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=api_key
        )

        # Gemini Embedding 2 supports
        # multiple output dimensions.
        #
        # 768 is suitable for our
        # FAISS vector index.
        self.output_dimension = 768

        # Maximum number of retries for
        # temporary Gemini API errors.
        self.max_retries = 6

    # =========================================================
    # GET RETRY DELAY
    # =========================================================

    def _get_retry_delay(
        self,
        error: Exception,
        attempt: int
    ) -> float:

        error_message = str(error)

        # Example:
        #
        # Please retry in 31.742373814s

        match = re.search(
            r"retry in ([0-9]+(?:\.[0-9]+)?)s",
            error_message,
            re.IGNORECASE
        )

        if match:

            delay = float(
                match.group(1)
            )

            return (
                delay
                + random.uniform(1, 3)
            )

        # Example:
        #
        # retryDelay: 31s

        match = re.search(
            r"retryDelay['\"]?\s*:\s*['\"]?([0-9]+)",
            error_message,
            re.IGNORECASE
        )

        if match:

            delay = float(
                match.group(1)
            )

            return (
                delay
                + random.uniform(1, 3)
            )

        # Fallback exponential backoff.
        #
        # attempt 0 -> 2 seconds
        # attempt 1 -> 4 seconds
        # attempt 2 -> 8 seconds
        # attempt 3 -> 16 seconds
        # attempt 4 -> 32 seconds
        # attempt 5 -> 60 seconds maximum

        delay = min(
            2 ** (attempt + 1),
            60
        )

        return (
            delay
            + random.uniform(0.5, 2)
        )

    # =========================================================
    # CHECK WHETHER ERROR IS RETRYABLE
    # =========================================================

    def _is_retryable_error(
        self,
        error: Exception
    ) -> bool:

        error_message = str(
            error
        ).lower()

        return (
            "429" in error_message
            or "resource_exhausted" in error_message
            or "rate limit" in error_message
            or "too many requests" in error_message
            or "503" in error_message
            or "service unavailable" in error_message
        )

    # =========================================================
    # EMBED ONE TEXT
    # =========================================================

    def embed_text(
        self,
        text: str
    ) -> list[float]:

        for attempt in range(
            self.max_retries
        ):

            try:

                response = (
                    self.client.models.embed_content(
                        model=self.model,
                        contents=text,
                        config=types.EmbedContentConfig(
                            output_dimensionality=(
                                self.output_dimension
                            )
                        )
                    )
                )

                # Make sure Gemini returned
                # an embedding.

                if not response.embeddings:

                    raise RuntimeError(
                        "Gemini returned no embedding."
                    )

                # Because we send ONE text,
                # Gemini should return ONE embedding.

                embedding = (
                    response.embeddings[0]
                )

                values = embedding.values

                if not values:

                    raise RuntimeError(
                        "Gemini returned an empty embedding."
                    )

                # Make sure the dimension is
                # what our FAISS index expects.

                if len(values) != self.output_dimension:

                    raise RuntimeError(
                        "Gemini returned an embedding "
                        f"with dimension {len(values)} "
                        f"instead of "
                        f"{self.output_dimension}."
                    )

                return values

            except APIError as exc:

                if not self._is_retryable_error(
                    exc
                ):

                    raise

                # All retries exhausted.

                if attempt >= (
                    self.max_retries - 1
                ):

                    raise RuntimeError(
                        "Failed to generate embedding "
                        "after multiple Gemini API retries."
                    ) from exc

                delay = (
                    self._get_retry_delay(
                        exc,
                        attempt
                    )
                )

                print(
                    "Gemini API temporary error."
                )

                print(
                    f"Retrying in "
                    f"{delay:.1f} seconds..."
                )

                time.sleep(
                    delay
                )

        raise RuntimeError(
            "Failed to generate embedding."
        )

    # =========================================================
    # EMBED MULTIPLE TEXTS
    # =========================================================

    def embed_texts(
        self,
        texts: list[str]
    ) -> list[list[float]]:

        if not texts:

            return []

        all_embeddings = []

        total_texts = len(
            texts
        )

        print(
            f"Generating embeddings for "
            f"{total_texts} texts..."
        )

        # IMPORTANT:
        #
        # We intentionally process ONE text
        # at a time.
        #
        # Our installed Gemini SDK returned
        # only ONE embedding when a list of
        # multiple strings was passed through
        # `contents`.
        #
        # Therefore we use embed_text()
        # for every individual chunk.

        for index, text in enumerate(
            texts
        ):

            print(
                f"Embedding text "
                f"{index + 1}/{total_texts}"
            )

            embedding = (
                self.embed_text(
                    text
                )
            )

            all_embeddings.append(
                embedding
            )

        print(
            "Embedding generation completed."
        )

        return all_embeddings

    # =========================================================
    # DOCUMENT EMBEDDING
    # =========================================================

    def embed_document(
        self,
        text: str,
        title: str = "none"
    ) -> list[float]:

        content = (
            f"title: {title}\n"
            f"text: {text}"
        )

        return self.embed_text(
            content
        )

    # =========================================================
    # QUERY EMBEDDING
    # =========================================================

    def embed_query(
        self,
        query: str
    ) -> list[float]:

        content = (
            "task: question answering\n"
            f"query: {query}"
        )

        return self.embed_text(
            content
        )