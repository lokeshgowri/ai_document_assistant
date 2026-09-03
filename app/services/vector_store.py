import json
from pathlib import Path

import faiss
import numpy as np


class VectorStore:

    def __init__(self, dimension: int):
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata = []

    def add_vectors(self, vectors, metadata):

        vectors_array = np.array(
            vectors,
            dtype="float32"
        )

        self.index.add(vectors_array)
        self.metadata.extend(metadata)

    def search(
        self,
        query_vector,
        top_k: int = 3,
        source: str | None = None,
        section: str | None = None,
        distance_threshold: float | None = None
    ):

        query_array = np.array(
            [query_vector],
            dtype="float32"
        )

        if source or section or distance_threshold is not None:
            search_k = self.index.ntotal
        else:
            search_k = top_k

        distances, indices = self.index.search(
            query_array,
            search_k
        )

        results = []

        for distance, index in zip(
            distances[0],
            indices[0]
        ):

            if index == -1:
                continue

            if (
                distance_threshold is not None
                and distance > distance_threshold
            ):
                continue

            metadata = self.metadata[index]

            if source:

                metadata_source = metadata.get(
                    "source"
                )

                if not metadata_source:
                    continue

                if source.lower() not in metadata_source.lower():
                    continue

            if section:

                metadata_section = metadata.get(
                    "section"
                )

                if not metadata_section:
                    continue

                if section.lower() not in metadata_section.lower():
                    continue

            results.append({
                "distance": float(distance),
                "metadata": metadata
            })

            if len(results) >= top_k:
                break

        return results

    def save(self, index_path: str):

        index_path = Path(index_path)

        index_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        faiss.write_index(
            self.index,
            str(index_path)
        )

        metadata_path = index_path.parent / "metadata.json"

        with open(
            metadata_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.metadata,
                file,
                ensure_ascii=False,
                indent=2
            )

    def load(self, index_path: str):

        index_path = Path(index_path)

        self.index = faiss.read_index(
            str(index_path)
        )

        metadata_path = index_path.parent / "metadata.json"

        with open(
            metadata_path,
            "r",
            encoding="utf-8"
        ) as file:

            self.metadata = json.load(file)