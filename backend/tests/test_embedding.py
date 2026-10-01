import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()


def main():

    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY")
    )

    texts = [
        "This is test document chunk one.",
        "This is test document chunk two.",
        "This is test document chunk three."
    ]

    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=texts,
        config=types.EmbedContentConfig(
            output_dimensionality=768
        )
    )

    print("RESPONSE TYPE:")
    print(type(response))

    print("\nRESPONSE:")
    print(response)

    print("\nEMBEDDINGS:")
    print(response.embeddings)

    print("\nNUMBER OF EMBEDDINGS:")
    print(len(response.embeddings))

    for index, embedding in enumerate(
        response.embeddings
    ):

        print(
            f"\nEmbedding {index}:"
        )

        print(
            "Type:",
            type(embedding)
        )

        print(
            "Attributes:",
            dir(embedding)
        )

        print(
            "Values length:",
            len(embedding.values)
        )


if __name__ == "__main__":

    main()