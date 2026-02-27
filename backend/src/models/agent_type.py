from enum import Enum


class AgentType(str, Enum):
    """Types of specialist agents available in the system"""
    ROUTER = "router"
    SYMPTOM = "symptom"
    MEDICATION = "medication"
    LIFESTYLE = "lifestyle"
    FALLBACK = "fallback"
