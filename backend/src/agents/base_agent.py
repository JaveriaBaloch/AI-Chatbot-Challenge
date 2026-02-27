from abc import ABC, abstractmethod
from typing import List, Optional
import os
from dotenv import load_dotenv
from google import genai
from ..models.agent_response import AgentResponse
from ..models.message import Message
from ..models.agent_type import AgentType
from ..models.conversation_context import ConversationContext

load_dotenv()


class BaseAgent(ABC):
    """Base class for all specialist agents"""
    
    def __init__(self, agent_type: AgentType, model: str = "gemini-flash-latest"):  # Corrected model name
        self.agent_type = agent_type
        self.model = model
        
        # Get API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Pass API key explicitly to the client
        self.client = genai.Client(api_key=api_key)
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent"""
        pass
    
    @abstractmethod
    def should_handle(self, query: str) -> bool:
        """Determine if this agent should handle the query"""
        pass
    
    def _prepare_prompt(
        self, 
        user_query: str, 
        context: Optional[ConversationContext] = None
    ) -> str:
        """Prepare prompt with system instructions and context"""
        prompt = self.get_system_prompt() + "\n\n"
        
        if context and context.messages:
            prompt += "Conversation history:\n"
            for msg in context.messages[-5:]:
                prompt += f"{msg.role}: {msg.content}\n"
            prompt += "\n"
        
        prompt += f"User: {user_query}\n\nAssistant:"
        
        return prompt
    
    async def process(
        self, 
        query: str, 
        context: Optional[ConversationContext] = None
    ) -> AgentResponse:
        """Process a query and return a response"""
        try:
            prompt = self._prepare_prompt(query, context)
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            content = response.text
            
            return AgentResponse(
                agent_type=self.agent_type,
                content=content,
                confidence=1.0,
                metadata={"model": self.model}
            )
            
        except Exception as e:
            return AgentResponse(
                agent_type=self.agent_type,
                content=f"I apologize, but I encountered an error processing your request. Please try again.",
                confidence=0.0,
                metadata={"error": str(e)}
            )
