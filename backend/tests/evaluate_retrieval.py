import faiss

from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.reranker import Reranker

from backend.tests.evaluation_dataset import evaluation_dataset


INDEX_PATH = "data/index.faiss"


def evaluate(distance_threshold):

    # ---------------------------------------------
    # Create services
    # ---------------------------------------------

    embedding_service = EmbeddingService()

    # Read the existing FAISS index
    saved_index = faiss.read_index(INDEX_PATH)

    # Get actual vector dimension
    dimension = saved_index.d

    # Create VectorStore with correct dimension
    vector_store = VectorStore(dimension)

    # Load FAISS index + metadata
    vector_store.load(INDEX_PATH)

    # Create reranker
    reranker = Reranker()

    # ---------------------------------------------
    # Evaluation metrics
    # ---------------------------------------------

    hit_at_3 = 0

    reciprocal_ranks = []

    precision_scores = []

    recall_scores = []

    # ---------------------------------------------
    # Evaluate every question
    # ---------------------------------------------

    for item in evaluation_dataset:

        question = item["question"]

        expected_source = item["expected_source"]

        expected_text = item["expected_text"]

        print("\n================================")
        print("Question:", question)

        # -----------------------------------------
        # Create query embedding
        # -----------------------------------------

        query_vector = embedding_service.embed_text(
            question
        )

        # -----------------------------------------
        # Retrieve top 10 from FAISS
        # -----------------------------------------

        results = vector_store.search(
            query_vector,
            top_k=10,
            distance_threshold=distance_threshold
        )

        # -----------------------------------------
        # Rerank top 10 and keep top 3
        # -----------------------------------------

        results = reranker.rerank(
            question,
            results,
            top_k=3
        )

        # -----------------------------------------
        # Track whether expected result was found
        # -----------------------------------------

        found_rank = None

        relevant_count = 0

        # -----------------------------------------
        # Check top 3 results
        # -----------------------------------------

        for rank, result in enumerate(
            results,
            start=1
        ):

            metadata = result["metadata"]

            source = metadata.get(
                "source",
                ""
            )

            text = metadata.get(
                "text",
                ""
            )

            rerank_score = result.get(
                "rerank_score"
            )

            print(
                f"Rank {rank}: "
                f"{source} | "
                f"Rerank Score: "
                f"{rerank_score}"
            )

            # -------------------------------------
            # Determine whether result is relevant
            # -------------------------------------

            if (
                expected_source.lower()
                in source.lower()
                and
                expected_text.lower()
                in text.lower()
            ):

                relevant_count += 1

                # Store FIRST relevant rank
                if found_rank is None:

                    found_rank = rank

        # -----------------------------------------
        # Hit@3 and MRR
        # -----------------------------------------

        if found_rank is not None:

            hit_at_3 += 1

            reciprocal_ranks.append(
                1 / found_rank
            )

            print(
                f"Result: CORRECT "
                f"(Rank {found_rank})"
            )

        else:

            reciprocal_ranks.append(0)

            print(
                "Result: INCORRECT"
            )

        # -----------------------------------------
        # Precision@3
        # -----------------------------------------

        precision_at_3 = (
            relevant_count / 3
        )

        precision_scores.append(
            precision_at_3
        )

        # -----------------------------------------
        # Recall@3
        # -----------------------------------------

        if found_rank is not None:

            recall_at_3 = 1

        else:

            recall_at_3 = 0

        recall_scores.append(
            recall_at_3
        )

    # ---------------------------------------------
    # Calculate final metrics
    # ---------------------------------------------

    total = len(
        evaluation_dataset
    )

    # Hit@3
    hit_rate = (
        hit_at_3 / total
    )

    # MRR
    mrr = (
        sum(reciprocal_ranks)
        / total
    )

    # Precision@3
    precision = (
        sum(precision_scores)
        / total
    )

    # Recall@3
    recall = (
        sum(recall_scores)
        / total
    )

    # ---------------------------------------------
    # Display evaluation results
    # ---------------------------------------------

    print("\n================================")
    print(
    f"RETRIEVAL EVALUATION "
    f"(Threshold: {distance_threshold})"
    )
    print("================================")

    print(
        f"Hit@3:       {hit_rate:.2f}"
    )

    print(
        f"MRR:         {mrr:.2f}"
    )

    print(
        f"Precision@3: {precision:.2f}"
    )

    print(
        f"Recall@3:    {recall:.2f}"
    )


if __name__ == "__main__":

    thresholds = [
        0.6,
        0.7,
        0.8,
        0.9,
        1.0
    ]

    for threshold in thresholds:

        print("\n\n")
        print("################################")
        print(
            f"TESTING THRESHOLD: {threshold}"
        )
        print("################################")

        evaluate(threshold)