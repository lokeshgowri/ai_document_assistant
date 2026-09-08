from pydantic import BaseModel, Field
from datetime import datetime

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

    conversation_id: int | None = Field(
        default=None,
        description="Conversation to which this question belongs."
    )


class Source(BaseModel):

    source: str
    text: str


class AskResponse(BaseModel):

    answer: str
    sources: list[Source]

from pydantic import BaseModel, ConfigDict


class ConversationCreate(BaseModel):
    title: str = "New Conversation"


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class ConversationDetailResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse]

    model_config = ConfigDict(
        from_attributes=True
    )