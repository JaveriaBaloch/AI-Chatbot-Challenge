from pydantic import BaseModel, Field


class Message(BaseModel):
    """Represents a single message in the conversation"""
    role: str = Field(..., description="Role of the message sender (user/assistant)")
    content: str = Field(..., description="Content of the message")
