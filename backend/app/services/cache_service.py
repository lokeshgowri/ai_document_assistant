import hashlib
import json
from datetime import datetime, timezone

from app.services.blob_service import BlobStorageService


class CacheService:
    """
    Persistent response cache using Vercel Blob.

    Cache entries are stored separately from:
    - conversations/
    - conversation-messages/
    - documents/
    - index/
    """

    CACHE_PREFIX = "cache/"

    def __init__(self):
        self.blob_service = BlobStorageService()

    def create_corpus_signature(self, metadata: list[dict]) -> str:
        """
        Create a stable signature representing the currently indexed documents.
        If documents are added, removed, or modified, the signature changes.
        """
        documents = {}
        for item in metadata:
            document_path = item.get("document_path")
            document_hash = item.get("document_hash")
            if not document_path:
                continue
            documents[document_path] = document_hash

        normalized_documents = sorted(
            documents.items(),
            key=lambda item: item[0]
            )

        serialized = json.dumps(
            normalized_documents,
            ensure_ascii=False,
            sort_keys=True,
            )

        return hashlib.sha256(
            serialized.encode("utf-8")
            ).hexdigest()


    def _create_cache_key(
        self,
        question: str,
        top_k: int = 3,
        source: str | None = None,
        section: str | None = None,
        corpus_signature: str = "",
    ) -> str:
        """
        Create a stable cache key from everything that can affect
        a document-grounded response.
        """

        cache_data = {
            "question": question.strip().lower(),
            "top_k": top_k,
            "source": source.strip().lower() if source else None,
            "section": section.strip().lower() if section else None,
            "corpus_signature": corpus_signature,
        }

        serialized = json.dumps(
            cache_data,
            sort_keys=True,
            ensure_ascii=False,
        )

        return hashlib.sha256(
            serialized.encode("utf-8")
        ).hexdigest()

    def _cache_path(self, cache_key: str) -> str:
        return f"{self.CACHE_PREFIX}{cache_key}.json"

    async def get(
        self,
        question: str,
        top_k: int = 3,
        source: str | None = None,
        section: str | None = None,
        corpus_signature: str = "",
    ):
        """
        Return cached response if available.
        Otherwise return None.
        """

        cache_key = self._create_cache_key(
            question=question,
            top_k=top_k,
            source=source,
            section=section,
            corpus_signature=corpus_signature,
        )

        pathname = self._cache_path(cache_key)

        try:
            result = await self.blob_service.get_file(pathname)

            if result is None:
                return None

            data = json.loads(result.content.decode("utf-8"))

            return data.get("response")

        except Exception:
            # Cache failure should NEVER break the application.
            return None

    async def set(
        self,
        question: str,
        response: dict,
        top_k: int = 3,
        source: str | None = None,
        section: str | None = None,
        corpus_signature: str = "",
    ):
        """
        Save a successful RAG response to the persistent cache.
        """

        cache_key = self._create_cache_key(
            question=question,
            top_k=top_k,
            source=source,
            section=section,
            corpus_signature=corpus_signature,
        )

        pathname = self._cache_path(cache_key)

        cache_data = {
            "cache_key": cache_key,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "response": response,
        }

        try:
            await self.blob_service.upload_file(
                pathname=pathname,
                data=json.dumps(
                    cache_data,
                    ensure_ascii=False,
                ).encode("utf-8"),
                content_type="application/json",
                overwrite=True,
            )

        except Exception:
            # Cache failure should NEVER break the application.
            pass