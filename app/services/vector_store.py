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

    def search(self, query_vector, top_k: int = 3):
        query_array = np.array(
            [query_vector],
            dtype="float32"
        )

        distances, indices = self.index.search(
            query_array,
            top_k
        )

        results = []

        for distance, index in zip(
            distances[0],
            indices[0]
        ):
            if index == -1:
                continue

            results.append({
                "distance": float(distance),
                "metadata": self.metadata[index]
            })

        return results

    def save(self, index_path: str):
        faiss.write_index(self.index, index_path)

    def load(self, index_path: str):
        self.index = faiss.read_index(index_path)