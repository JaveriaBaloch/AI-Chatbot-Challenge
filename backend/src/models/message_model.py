from pydantic import BaseModel, Field
from typing import Optional


class MessageModel(BaseModel):
    """Model for incoming chat messages from frontend"""
    text: str = Field(..., description="User's message text")
    session_id: Optional[str] = Field(None, description="Session ID for the conversation")