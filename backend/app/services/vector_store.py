import json
from pathlib import Path

import faiss
import numpy as np


class VectorStore:

    def __init__(self, dimension: int):
        base_index = faiss.IndexFlatL2(dimension)

        self.index = faiss.IndexIDMap2(base_index)

        self.metadata = []

        self.id_to_metadata_index = {}

        self.next_vector_id = 0

    # ---------------------------------------------------------
    # ADD VECTORS
    # ---------------------------------------------------------

    def add_vectors(self, vectors, metadata):
        vectors_array = np.asarray(
            vectors,
            dtype="float32"
        )

        if len(vectors_array) != len(metadata):
            raise ValueError(
                "Number of vectors must match number of metadata entries."
            )

        if len(vectors_array) == 0:
            return

        vector_ids = np.arange(
            self.next_vector_id,
            self.next_vector_id + len(vectors_array),
            dtype=np.int64
        )

        # Explicitly make sure the index is ID-mapped.
        if not isinstance(
            self.index,
            faiss.IndexIDMap2
        ):
            self.index = faiss.IndexIDMap2(
                self.index
            )

        self.index.add_with_ids(
            vectors_array,
            vector_ids
        )

        start_metadata_index = len(
            self.metadata
        )

        self.metadata.extend(
            metadata
        )

        for offset, vector_id in enumerate(
            vector_ids
        ):

            metadata_index = (
                start_metadata_index + offset
            )

            self.id_to_metadata_index[
                int(vector_id)
            ] = metadata_index

        self.next_vector_id += len(
            vector_ids
        )

    # ---------------------------------------------------------
    # REMOVE DOCUMENT
    # ---------------------------------------------------------

    def remove_document(self, document_path: str):

        vector_ids_to_remove = []

        for vector_id, metadata_index in self.id_to_metadata_index.items():

            metadata = self.metadata[metadata_index]

            if metadata.get("document_path") == document_path:
                vector_ids_to_remove.append(vector_id)

        if not vector_ids_to_remove:
            return 0

        ids_array = np.array(
            vector_ids_to_remove,
            dtype=np.int64
        )

        self.index.remove_ids(ids_array)

        # Remove metadata entries belonging to the document.
        remaining_metadata = []
        remaining_mapping = {}

        for vector_id, metadata_index in self.id_to_metadata_index.items():

            if vector_id in vector_ids_to_remove:
                continue

            new_metadata_index = len(remaining_metadata)

            remaining_metadata.append(
                self.metadata[metadata_index]
            )

            remaining_mapping[
                vector_id
            ] = new_metadata_index

        self.metadata = remaining_metadata
        self.id_to_metadata_index = remaining_mapping

        return len(vector_ids_to_remove)

    # ---------------------------------------------------------
    # SEARCH
    # ---------------------------------------------------------

    def search(
        self,
        query_vector,
        top_k: int = 3,
        source: str | None = None,
        section: str | None = None,
        distance_threshold: float | None = None,
        conversation_id: int | None = None,
        global_only: bool = False
    ):

        query_array = np.array(
            [query_vector],
            dtype="float32"
        )

        if self.index.ntotal == 0:
            return []

        if (
            source
            or section
            or distance_threshold is not None
            or conversation_id is not None
            or global_only
        ):
            search_k = self.index.ntotal
        else:
            search_k = min(
                top_k,
                self.index.ntotal
            )

        distances, vector_ids = self.index.search(
            query_array,
            search_k
        )

        results = []

        for distance, vector_id in zip(
            distances[0],
            vector_ids[0]
        ):

            if vector_id == -1:
                continue

            vector_id = int(vector_id)

            metadata_index = self.id_to_metadata_index.get(
                vector_id
            )

            if metadata_index is None:
                continue

            metadata = self.metadata[metadata_index]

            # -------------------------------------------------
            # Distance filtering
            # -------------------------------------------------

            if (
                distance_threshold is not None
                and distance > distance_threshold
            ):
                continue

            # -------------------------------------------------
            # Conversation-specific filtering
            # -------------------------------------------------

            if conversation_id is not None:

                metadata_conversation_id = metadata.get(
                    "conversation_id"
                )

                if (
                    metadata_conversation_id
                    != conversation_id
                ):
                    continue

            # -------------------------------------------------
            # Global document filtering
            #
            # Global documents have:
            # conversation_id = None
            # -------------------------------------------------

            elif global_only:

                if metadata.get("conversation_id") is not None:
                    continue

            # -------------------------------------------------
            # Source filtering
            # -------------------------------------------------

            if source:

                metadata_source = metadata.get(
                    "source"
                )

                if not metadata_source:
                    continue

                if source.lower() not in metadata_source.lower():
                    continue

            # -------------------------------------------------
            # Section filtering
            # -------------------------------------------------

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

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------

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
                {
                    "metadata": self.metadata,
                    "id_to_metadata_index": self.id_to_metadata_index,
                    "next_vector_id": self.next_vector_id
                },
                file,
                ensure_ascii=False,
                indent=2
            )

    # ---------------------------------------------------------
    # LOAD
    # ---------------------------------------------------------

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

            saved_data = json.load(file)

        # New metadata format
        if isinstance(saved_data, dict):

            self.metadata = saved_data.get(
                "metadata",
                []
            )

            self.id_to_metadata_index = {
                int(vector_id): int(metadata_index)
                for vector_id, metadata_index
                in saved_data.get(
                    "id_to_metadata_index",
                    {}
                ).items()
            }

            self.next_vector_id = saved_data.get(
                "next_vector_id",
                0
            )

        # Old metadata format
        else:
            self.metadata = saved_data

            self.id_to_metadata_index = {}

            # This branch is mainly for detecting
            # old indexes. The old IndexFlatL2
            # does not contain custom vector IDs.
            for metadata_index in range(
                len(self.metadata)
            ):
                self.id_to_metadata_index[
                    metadata_index
                ] = metadata_index

            self.next_vector_id = len(
                self.metadata
            )