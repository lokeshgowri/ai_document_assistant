from app.services.indexing_service import IndexingService


if __name__ == "__main__":

    indexing_service = IndexingService()

    result = indexing_service.build_index()

    print("\nINDEXING RESULT:")
    print(result)