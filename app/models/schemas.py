from pydantic import BaseModel, Field


# Defines the data sent to and returned from the API.
class AskRequest(BaseModel):

    question: str = Field(
        ...,
        min_length=1,
        description="Question to ask about the indexed documents."
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of final results to use."
    )

    source: str | None = Field(
        default=None,
        description="Optional source document filter."
    )

    section: str | None = Field(
        default=None,
        description="Optional document section filter."
    )


class Source(BaseModel):

    source: str
    text: str


class AskResponse(BaseModel):

    answer: str
    sources: list[Source]