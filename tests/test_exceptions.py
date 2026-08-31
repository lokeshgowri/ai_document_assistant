from app.exceptions import DocumentProcessingError


try:
    raise DocumentProcessingError("Test document processing error")
except DocumentProcessingError as e:
    print("Caught:", e)