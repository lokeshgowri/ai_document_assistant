import faiss
import numpy as np
import json
from pathlib import Path


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
        section: str | None = None
    ):

        query_array = np.array(
            [query_vector],
            dtype="float32"
        )

        # If filtering is requested, retrieve all vectors
        # so that we can apply the metadata filter afterward.
        if source or section:
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

            metadata = self.metadata[index]

            #Apply source filter
            if source:

                metadata_source = metadata.get(
                    "source"
                )

                if not metadata_source:
                    continue

                if source.lower() not in metadata_source.lower():
                    continue

            # Apply section filter
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

            # Stop after getting requested number of results
            if len(results) >= top_k:
                break

        return results

    def save(self, index_path: str):

        # Convert path to Path object
        index_path = Path(index_path)

        # Make sure the directory exists
        index_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # Save FAISS index
        faiss.write_index(
            self.index,
            str(index_path)
        )

        # Save metadata
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

        # Convert path to Path object
        index_path = Path(index_path)

        # Load FAISS index
        self.index = faiss.read_index(
            str(index_path)
        )

        # Load metadata
        metadata_path = index_path.parent / "metadata.json"

        with open(
            metadata_path,
            "r",
            encoding="utf-8"
        ) as file:

            self.metadata = json.load(file)