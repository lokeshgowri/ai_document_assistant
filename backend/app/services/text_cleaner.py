import re


def clean_text(text: str) -> str:
    """
    Clean extracted document text while preserving its meaning.
    """

    if not isinstance(text, str):
        raise TypeError(
            "text must be a string"
        )

    text = text.strip()

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text