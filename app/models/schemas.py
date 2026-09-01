from pydantic import BaseModel, Field
#Schema defines the state of the data that is sent to the API and the data that is returned from the API.

class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="Question to ask about the uploaded documents."
    )
    top_k: int = Field(
        default=3,
        ge=1,
        description="Number of relevant chunks to retrieve."
    )

class Source(BaseModel):
    source: str
    text: str

class AskResponse(BaseModel):
    answer: str
    sources: list[Source]