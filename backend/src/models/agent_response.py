from pydantic import BaseModel, Field
from typing import Optional
from .agent_type import AgentType


class AgentResponse(BaseModel):
    """Response from an agent after processing a query"""
    agent_type: AgentType
    content: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    requires_handoff: bool = Field(default=False)
    handoff_to: Optional[AgentType] = None
    metadata: dict = Field(default_factory=dict)
