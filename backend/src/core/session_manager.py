"""
Session management for chat conversations
"""
from typing import Dict, Optional
from pathlib import Path
import json
from datetime import datetime
import logging

from ..models.conversation_context import ConversationContext

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages chat sessions and conversation contexts"""
    
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        self.prompts_dir.mkdir(exist_ok=True)
        self.conversations: Dict[str, ConversationContext] = {}
        self.current_session_id: Optional[str] = None
    
    def get_context(self, session_id: str) -> ConversationContext:
        """Get or create conversation context for a session"""
        if session_id not in self.conversations:
            self.conversations[session_id] = ConversationContext()
        return self.conversations[session_id]
    
    def set_current_session(self, session_id: str):
        """Set the current active session"""
        self.current_session_id = session_id
    
    def save_chat_history(self, session_id: str, user_message: str, agent_response: dict):
        """Save chat interaction to prompts directory"""
        try:
            chat_file = self.prompts_dir / f"chat_history_{session_id}.json"
            
            # Load existing history or create new
            if chat_file.exists():
                with open(chat_file, 'r') as f:
                    history = json.load(f)
            else:
                history = {
                    "session_id": session_id,
                    "started_at": datetime.utcnow().isoformat() + "Z",
                    "messages": []
                }
            
            # Add new interaction
            history["messages"].append({
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "user": user_message,
                "agent": agent_response["agent"],
                "response": agent_response["processed"],
                "confidence": agent_response["confidence"],
                "metadata": agent_response.get("metadata", {})
            })
            
            history["last_updated"] = datetime.utcnow().isoformat() + "Z"
            
            # Save updated history
            with open(chat_file, 'w') as f:
                json.dump(history, f, indent=2)
            
            logger.info(f"Saved chat history to {chat_file}")
        except Exception as e:
            logger.error(f"Failed to save chat history: {e}")
