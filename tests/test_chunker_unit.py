from app.services.chunker import chunk_text


def test_chunk_text_creates_chunks():

    text = (
        "Company Leave Policy. "
        "Employees are entitled to annual leave. "
        "Leave requests must be submitted through HR. "
        "Employees should follow the company leave procedure."
    )

    chunks = chunk_text(
        text,
        chunk_size=50,
        chunk_overlap=10
    )

    assert len(chunks) > 1


def test_chunk_text_empty_input():

    chunks = chunk_text(
        "",
        chunk_size=50,
        chunk_overlap=10
    )

    assert chunks == []