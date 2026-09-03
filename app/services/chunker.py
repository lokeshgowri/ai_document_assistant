import re


def is_heading(line: str) -> bool:
    """
    Detect whether a line looks like a document heading.
    """

    line = line.strip()

    if not line:
        return False

    if re.match(r"^\d+[\.\)]\s+", line):
        return True

    if line.isupper() and len(line) <= 100:
        return True

    return False


def split_into_sections(text: str) -> list[dict]:
    """
    Split document text into logical sections.
    """

    lines = text.splitlines()

    sections = []

    current_heading = None
    current_lines = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        if is_heading(line):

            if current_lines:
                sections.append({
                    "heading": current_heading,
                    "text": "\n".join(current_lines)
                })

            current_heading = line
            current_lines = []

        else:
            current_lines.append(line)

    if current_lines:
        sections.append({
            "heading": current_heading,
            "text": "\n".join(current_lines)
        })

    return sections


def chunk_text_with_metadata(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[dict]:
    """
    Split text into structure-aware chunks
    while preserving section metadata.
    """

    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than 0"
        )

    if chunk_overlap < 0:
        raise ValueError(
            "chunk_overlap cannot be negative"
        )

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size"
        )

    sections = split_into_sections(text)

    chunks = []

    for section in sections:

        heading = section["heading"]
        section_text = section["text"]

        sentences = re.split(
            r"(?<=[.!?])\s+",
            section_text
        )

        sentences = [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

        current_sentences = []
        current_length = 0

        for sentence in sentences:

            sentence_length = len(sentence)

            if (
                current_sentences
                and current_length
                + sentence_length
                + 1
                > chunk_size
            ):

                chunk_text_value = " ".join(
                    current_sentences
                )

                chunks.append({
                    "section": heading,
                    "text": chunk_text_value.strip()
                })

                overlap_sentences = []
                overlap_length = 0

                for previous_sentence in reversed(
                    current_sentences
                ):

                    if (
                        overlap_length
                        + len(previous_sentence)
                        + 1
                        <= chunk_overlap
                    ):

                        overlap_sentences.insert(
                            0,
                            previous_sentence
                        )

                        overlap_length += (
                            len(previous_sentence) + 1
                        )

                    else:
                        break

                current_sentences = overlap_sentences
                current_length = overlap_length

            current_sentences.append(sentence)

            current_length += (
                sentence_length + 1
            )

        if current_sentences:

            chunk_text_value = " ".join(
                current_sentences
            )

            chunks.append({
                "section": heading,
                "text": chunk_text_value.strip()
            })

    return chunks


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[str]:
    """
    Backward-compatible chunking function.
    """

    structured_chunks = chunk_text_with_metadata(
        text,
        chunk_size,
        chunk_overlap
    )

    return [
        chunk["text"]
        for chunk in structured_chunks
    ]