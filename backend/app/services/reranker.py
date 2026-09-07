from sentence_transformers import CrossEncoder


class Reranker:

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ):
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        question: str,
        results: list[dict],
        top_k: int = 3
    ):

        if not results:
            return []

        pairs = []

        for result in results:

            text = result["metadata"]["text"]

            pairs.append(
                [question, text]
            )

        scores = self.model.predict(pairs)

        reranked_results = []

        for result, score in zip(
            results,
            scores
        ):

            result["rerank_score"] = float(score)

            reranked_results.append(result)

        reranked_results.sort(
            key=lambda x: x["rerank_score"],
            reverse=True
        )

        return reranked_results[:top_k]