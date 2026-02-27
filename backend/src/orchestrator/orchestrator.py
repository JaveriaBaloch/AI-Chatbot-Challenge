from typing import Dict, Optional
import os
from urllib import response
from dotenv import load_dotenv
import google.generativeai as genai
import logging
import json
from ..models.agent_type import AgentType
from ..models.conversation_context import ConversationContext
from ..models.agent_response import AgentResponse
from ..models.message import Message
from ..models.routing_decision import RoutingDecision
from ..agents.base_agent import BaseAgent
from ..agents.symptom_agent import SymptomAgent
from ..agents.medication_agent import MedicationAgent
from ..agents.lifestyle_agent import LifestyleAgent
from ..agents.fallback_agent import FallbackAgent

# Load environment variables from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Central orchestrator that routes queries to appropriate specialist agents.
    Uses Google Gemini to make intelligent routing decisions.
    """
    
    def __init__(self, model: str = "gemini-flash-latest"):  # Corrected model name
        self.model = model
        
        # Verify API key exists
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        logger.info(f"API Key found: {api_key[:10]}...")
        
        try:
            # Pass API key explicitly to the client
            self.client = genai.configure(api_key=api_key)
            self.model_client = genai.GenerativeModel(self.model)
            logger.info(f"Gemini client initialized with model: {model}")
        except Exception as e:
            logger.error(f"Failed to create Gemini client: {e}")
            raise
        
        # Initialize specialist agents
        self.agents: Dict[AgentType, BaseAgent] = {
            AgentType.SYMPTOM: SymptomAgent(),
            AgentType.MEDICATION: MedicationAgent(),
            AgentType.LIFESTYLE: LifestyleAgent(),
            AgentType.FALLBACK: FallbackAgent(),
        }
        
        logger.info(f"Initialized {len(self.agents)} specialist agents")
        
        self.router_prompt = self._get_router_system_prompt()
    
    def _get_router_system_prompt(self) -> str:
        """System prompt for the router agent"""
        return """You are a healthcare query router. Your job is to analyze user queries and determine which specialist agent should handle them.

Available Specialist Agents:
1. SYMPTOM - Handles questions about symptoms, their severity, when to seek care, pain descriptions, physical sensations
2. MEDICATION - Handles questions about medications, dosages, drug interactions, side effects, prescriptions, AND follow-up questions about which specialist to see for medication concerns, AND requests to book appointments related to medication questions
3. LIFESTYLE - Handles questions about diet, exercise, daily routines, stress management, sleep, nutrition
4. FALLBACK - For general questions, greetings, or queries outside the above domains

Guidelines:
- If a query mentions both symptoms AND medication, choose SYMPTOM (symptoms are higher priority for safety)
- If a query is about medication side effects causing symptoms, choose SYMPTOM
- Only choose MEDICATION if the query is purely about medication information without symptom concerns
- **IMPORTANT**: If user asks "which specialist" or "who should I see" as a follow-up to a medication question, route to MEDICATION agent
- **IMPORTANT**: If user asks to "book an appointment" or "schedule" after a medication discussion, route to MEDICATION agent
- **IMPORTANT**: If user asks to "book an appointment" or "I need an appointment" WITHOUT context, route to the last agent they spoke with, or FALLBACK if no context
- Choose LIFESTYLE for wellness, prevention, and daily health management questions
- Choose FALLBACK for casual conversation, unclear queries, or non-health topics, AND for generic appointment requests without prior health discussion

Context-Aware Routing:
- Consider the conversation history when available
- If the previous query was about medications and user asks "which specialist should I visit", route to MEDICATION
- If the previous query was about medications and user asks to "book an appointment", route to MEDICATION
- If the previous query was about symptoms and user asks "which specialist should I visit", route to SYMPTOM
- If the previous query was about symptoms and user asks to "book an appointment", route to SYMPTOM
- If the previous query was about lifestyle and user asks to "book an appointment", route to LIFESTYLE
- If user asks to "book an appointment" with NO prior context, route to FALLBACK (they need to select specialist type first)

Respond in this exact JSON format:
{
    "target_agent": "SYMPTOM|MEDICATION|LIFESTYLE|FALLBACK",
    "reasoning": "brief explanation of your decision",
    "confidence": 0.0-1.0
}

Only output valid JSON, no additional text."""
    
    async def _route_query(self, query: str, context: Optional[ConversationContext] = None) -> RoutingDecision:
        """Use LLM to determine which agent should handle the query"""
        try:
            # Include context in routing if available
            context_info = ""
            if context and context.current_agent:
                context_info = f"\n\nPrevious message context: User's last query was handled by the {context.current_agent.value.upper()} agent."
            
            prompt = f"{self.router_prompt}{context_info}\n\nRoute this query: {query}"
            
            logger.info(f"Routing query with {self.model}")
            
            response = self.model_client.generate_content(prompt)
            content = response.text.strip()
            
            logger.info(f"Router response: {content}")
            
            # Parse JSON response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            routing_data = json.loads(content)
            
            decision = RoutingDecision(
                target_agent=AgentType(routing_data["target_agent"].lower()),
                reasoning=routing_data["reasoning"],
                confidence=float(routing_data["confidence"])
            )
            
            logger.info(f"Routed to {decision.target_agent.value} agent (confidence: {decision.confidence})")
            
            return decision
            
        except Exception as e:
            logger.error(f"Error during routing: {str(e)}", exc_info=True)
            return RoutingDecision(
                target_agent=AgentType.FALLBACK,
                reasoning=f"Error during routing: {str(e)}",
                confidence=0.5
            )
    
    async def process_query(
        self, 
        query: str, 
        context: Optional[ConversationContext] = None
    ) -> AgentResponse:
        """
        Main entry point: route the query and get response from appropriate agent
        
        Args:
            query: User's input query
            context: Optional conversation context with history
            
        Returns:
            AgentResponse from the selected specialist agent
        """
        if context is None:
            context = ConversationContext()
        
        # Route the query
        routing_decision = await self._route_query(query, context)
        
        # Get the appropriate agent (should always exist now)
        agent = self.agents.get(routing_decision.target_agent)
        
        if not agent:
            # This should not happen, but provide a safety fallback
            agent = self.agents.get(AgentType.FALLBACK)
        
        # Process with selected agent
        response = await agent.process(query, context)
        
        # Add routing metadata
        response.metadata["routing"] = routing_decision.dict()
        
        return response
    
    def update_context(
        self, 
        context: ConversationContext, 
        user_query: str, 
        agent_response: AgentResponse
    ) -> ConversationContext:
        """Update conversation context with new messages"""
        context.messages.append(Message(role="user", content=user_query))
        context.messages.append(Message(role="assistant", content=agent_response.content))
        context.current_agent = agent_response.agent_type
        
        # Keep only last 10 messages (5 exchanges) to maintain context without overload
        if len(context.messages) > 10:
            context.messages = context.messages[-10:]
        
        return context
