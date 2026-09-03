import re

from rank_bm25 import BM25Okapi


class KeywordSearch:

    def __init__(self, metadata: list[dict]):

        self.metadata = metadata

        self.tokenized_documents = [
            self.tokenize(item.get("text", ""))
            for item in metadata
        ]

        if self.tokenized_documents:
            self.bm25 = BM25Okapi(
                self.tokenized_documents
            )
        else:
            self.bm25 = None

    @staticmethod
    def tokenize(text: str) -> list[str]:

        return re.findall(
            r"\b\w+\b",
            text.lower()
        )

    def search(
        self,
        query: str,
        top_k: int = 10
    ):

        if not self.metadata or self.bm25 is None:
            return []

        query_tokens = self.tokenize(query)

        scores = self.bm25.get_scores(
            query_tokens
        )

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )

        results = []

        for index in ranked_indices[:top_k]:

            results.append({
                "keyword_score": float(scores[index]),
                "metadata": self.metadata[index]
            })

        return results