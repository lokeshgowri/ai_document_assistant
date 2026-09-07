from app.services.document_loader import load_document


txt_document = load_document("data/sample.txt")

print("TXT:")
print(txt_document)


pdf_document = load_document("data/sample.pdf")

print("\nPDF:")
print(pdf_document)


docx_document = load_document("data/sample.docx")

print("\nDOCX:")
print(docx_document)