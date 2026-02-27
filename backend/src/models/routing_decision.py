from pydantic import BaseModel, Field
from .agent_type import AgentType


class RoutingDecision(BaseModel):
    """Router's decision on which agent should handle a query"""
    target_agent: AgentType
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
