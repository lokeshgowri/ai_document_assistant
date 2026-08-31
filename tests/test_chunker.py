from app.services.chunker import chunk_text


text = """
Company Leave Policy

Employees are entitled to 20 days of annual leave per year.

Employees should submit leave requests through the HR portal.

Leave requests should be submitted at least three working days in advance.
"""


chunks = chunk_text(
    text,
    chunk_size=100,
    chunk_overlap=20,
)


for index, chunk in enumerate(chunks, start=1):
    print(f"\n--- Chunk {index} ---")
    print(chunk)