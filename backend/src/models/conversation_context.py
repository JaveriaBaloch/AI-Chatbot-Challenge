from pydantic import BaseModel, Field
from typing import Optional, List
from .agent_type import AgentType
from .message import Message


class ConversationContext(BaseModel):
    """Context for maintaining conversation history and state"""
    messages: List[Message] = Field(default_factory=list)
    current_agent: Optional[AgentType] = None
    metadata: dict = Field(default_factory=dict)
