import logging
import random
import re
import time

import requests
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import (
    EMBEDDING_PROVIDER,
    EMBEDDING_MODEL,
    GEMINI_API_KEY,
    OLLAMA_BASE_URL,
    OLLAMA_EMBEDDING_MODEL,
)


logger = logging.getLogger(__name__)


class EmbeddingService:

    def __init__(self):

        self.provider = EMBEDDING_PROVIDER

        # --------------------------------------------------
        # Gemini
        # --------------------------------------------------

        if self.provider == "gemini":

            if not GEMINI_API_KEY:
                raise RuntimeError(
                    "GEMINI_API_KEY is not configured."
                )

            self.model = EMBEDDING_MODEL or "gemini-embedding-2"

            self.client = genai.Client(
                api_key=GEMINI_API_KEY
            )

            self.output_dimension = 768

            self.max_retries = 6

            logger.info(
                "Embedding provider initialized: Gemini (%s, %s dimensions)",
                self.model,
                self.output_dimension
            )

        # --------------------------------------------------
        # Ollama
        # --------------------------------------------------

        elif self.provider == "ollama":

            self.model = OLLAMA_EMBEDDING_MODEL

            self.base_url = OLLAMA_BASE_URL.rstrip("/")

            # The dimension will be detected from the first
            # generated embedding instead of being hard-coded.
            self.output_dimension = None

            logger.info(
                "Embedding provider initialized: Ollama (%s)",
                self.model
            )

        else:

            raise RuntimeError(
                f"Unsupported embedding provider: "
                f"{self.provider}"
            )

    # ======================================================
    # PUBLIC INFORMATION
    # ======================================================

    def get_provider_info(self) -> dict:

        return {
            "provider": self.provider,
            "model": self.model,
            "dimension": self.output_dimension
        }

    # ======================================================
    # GEMINI RETRY HELPERS
    # ======================================================

    def _get_retry_delay(
        self,
        error: Exception,
        attempt: int
    ) -> float:

        error_message = str(error)

        # Example:
        # Please retry in 31.742373814s

        match = re.search(
            r"retry in ([0-9]+(?:\.[0-9]+)?)s",
            error_message,
            re.IGNORECASE
        )

        if match:

            return (
                float(match.group(1))
                + random.uniform(1, 3)
            )

        # Example:
        # retryDelay: 31s

        match = re.search(
            r"retryDelay['\"]?\s*:\s*['\"]?([0-9]+)",
            error_message,
            re.IGNORECASE
        )

        if match:

            return (
                float(match.group(1))
                + random.uniform(1, 3)
            )

        # Fallback exponential backoff.

        delay = min(
            2 ** (attempt + 1),
            60
        )

        return (
            delay
            + random.uniform(0.5, 2)
        )

    def _is_retryable_error(
        self,
        error: Exception
    ) -> bool:

        error_message = str(error).lower()

        return (
            "429" in error_message
            or "resource_exhausted" in error_message
            or "rate limit" in error_message
            or "too many requests" in error_message
            or "503" in error_message
            or "service unavailable" in error_message
        )

    # ======================================================
    # EMBED ONE TEXT
    # ======================================================

    def embed_text(
        self,
        text: str
    ) -> list[float]:

        if not text or not text.strip():
            raise ValueError(
                "Text cannot be empty."
            )

        if self.provider == "gemini":

            return self._embed_gemini(text)

        if self.provider == "ollama":

            return self._embed_ollama(text)

        raise RuntimeError(
            f"Unsupported embedding provider: "
            f"{self.provider}"
        )

    # ======================================================
    # GEMINI EMBEDDING
    # ======================================================

    def _embed_gemini(
        self,
        text: str
    ) -> list[float]:

        for attempt in range(self.max_retries):

            try:

                response = self.client.models.embed_content(
                    model=self.model,
                    contents=text,
                    config=types.EmbedContentConfig(
                        output_dimensionality=self.output_dimension
                    )
                )

                if not response.embeddings:

                    raise RuntimeError(
                        "Gemini returned no embedding."
                    )

                values = response.embeddings[0].values

                if not values:

                    raise RuntimeError(
                        "Gemini returned an empty embedding."
                    )

                if len(values) != self.output_dimension:

                    raise RuntimeError(
                        "Gemini returned an embedding "
                        f"with dimension {len(values)} "
                        f"instead of "
                        f"{self.output_dimension}."
                    )

                return values

            except APIError as exc:

                if not self._is_retryable_error(exc):
                    raise

                if attempt >= self.max_retries - 1:

                    raise RuntimeError(
                        "Failed to generate embedding "
                        "after multiple Gemini API retries."
                    ) from exc

                delay = self._get_retry_delay(
                    exc,
                    attempt
                )

                logger.warning(
                    "Gemini embedding request failed temporarily. "
                    "Retrying in %.1f seconds...",
                    delay
                )

                time.sleep(delay)

    # ======================================================
    # OLLAMA EMBEDDING
    # ======================================================

    def _embed_ollama(
        self,
        text: str
    ) -> list[float]:

        try:

            response = requests.post(
                f"{self.base_url}/api/embed",
                json={
                    "model": self.model,
                    "input": text
                },
                timeout=120
            )

            response.raise_for_status()

            data = response.json()

            embeddings = data.get("embeddings")

            if not embeddings:

                raise RuntimeError(
                    "Ollama returned no embedding."
                )

            values = embeddings[0]

            if not values:

                raise RuntimeError(
                    "Ollama returned an empty embedding."
                )

            if self.output_dimension is None:

                self.output_dimension = len(values)

                logger.info(
                    "Ollama embedding dimension detected: %s",
                    self.output_dimension
                )

            elif len(values) != self.output_dimension:

                raise RuntimeError(
                    "Ollama returned an embedding "
                    f"with dimension {len(values)} "
                    f"instead of "
                    f"{self.output_dimension}."
                )

            return values

        except requests.exceptions.RequestException as exc:

            logger.exception(
                "Ollama embedding request failed."
            )

            raise RuntimeError(
                "Failed to connect to Ollama for embeddings. "
                "Make sure Ollama is running and the embedding "
                "model is available."
            ) from exc

    # ======================================================
    # EMBED MULTIPLE TEXTS
    # ======================================================

    def embed_texts(
        self,
        texts: list[str]
    ) -> list[list[float]]:

        if not texts:
            return []

        if self.provider == "ollama":

            return [
                self._embed_ollama(text)
                for text in texts
            ]

        # Gemini batch embedding

        all_embeddings = []

        batch_size = 10

        total_texts = len(texts)

        logger.info(
            "Embedding %s texts using Gemini in batches of %s.",
            total_texts,
            batch_size
        )

        for start in range(
            0,
            total_texts,
            batch_size
        ):

            batch = texts[
                start:start + batch_size
            ]

            try:

                response = self.client.models.embed_content(
                    model=self.model,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        output_dimensionality=self.output_dimension
                    )
                )

                if (
                    not response.embeddings
                    or len(response.embeddings) != len(batch)
                ):

                    logger.warning(
                        "Gemini batch response was invalid. "
                        "Falling back to individual requests."
                    )

                    for text in batch:

                        all_embeddings.append(
                            self._embed_gemini(text)
                        )

                    continue

                for embedding in response.embeddings:

                    values = embedding.values

                    if not values:

                        raise RuntimeError(
                            "Gemini returned an empty embedding."
                        )

                    if len(values) != self.output_dimension:

                        raise RuntimeError(
                            "Gemini returned an embedding "
                            f"with dimension {len(values)} "
                            f"instead of "
                            f"{self.output_dimension}."
                        )

                    all_embeddings.append(values)

            except APIError as exc:

                if not self._is_retryable_error(exc):
                    raise

                logger.warning(
                    "Gemini batch embedding request failed "
                    "temporarily. Falling back to individual "
                    "requests."
                )

                for text in batch:

                    all_embeddings.append(
                        self._embed_gemini(text)
                    )

        logger.info(
            "Embedding generation completed: %s embeddings.",
            len(all_embeddings)
        )

        return all_embeddings

    # ======================================================
    # DOCUMENT EMBEDDING
    # ======================================================

    def embed_document(
        self,
        text: str,
        title: str = "none"
    ) -> list[float]:

        content = (
            f"title: {title}\n"
            f"text: {text}"
        )

        return self.embed_text(content)

    # ======================================================
    # QUERY EMBEDDING
    # ======================================================

    def embed_query(
        self,
        query: str
    ) -> list[float]:

        content = (
            "task: question answering\n"
            f"query: {query}"
        )

        return self.embed_text(content)