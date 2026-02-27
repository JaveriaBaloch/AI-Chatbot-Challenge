"""
Test cases for SessionManager
"""
import pytest
from pathlib import Path
import shutil
import json
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.session_manager import SessionManager
from src.models.conversation_context import ConversationContext


@pytest.fixture
def test_prompts_dir(tmp_path):
    """Create temporary prompts directory for testing"""
    prompts_dir = tmp_path / "test_prompts"
    prompts_dir.mkdir()
    yield prompts_dir
    # Cleanup is automatic with tmp_path


@pytest.fixture
def session_manager(test_prompts_dir):
    """Create SessionManager instance for testing"""
    return SessionManager(test_prompts_dir)


class TestSessionManagerInitialization:
    """Test SessionManager initialization"""
    
    def test_initialization(self, test_prompts_dir):
        """Test SessionManager initializes correctly"""
        manager = SessionManager(test_prompts_dir)
        assert manager.prompts_dir == test_prompts_dir
        assert test_prompts_dir.exists()
        assert manager.conversations == {}
        assert manager.current_session_id is None
    
    def test_creates_prompts_directory(self, tmp_path):
        """Test SessionManager creates prompts directory if not exists"""
        new_dir = tmp_path / "new_prompts"
        assert not new_dir.exists()
        
        manager = SessionManager(new_dir)
        assert new_dir.exists()


class TestContextManagement:
    """Test conversation context management"""
    
    def test_get_context_creates_new(self, session_manager):
        """Test get_context creates new context for new session"""
        session_id = "test_session_1"
        context = session_manager.get_context(session_id)
        
        assert isinstance(context, ConversationContext)
        assert session_id in session_manager.conversations
        assert session_manager.conversations[session_id] == context
    
    def test_get_context_returns_existing(self, session_manager):
        """Test get_context returns existing context"""
        session_id = "test_session_2"
        
        # Get context first time
        context1 = session_manager.get_context(session_id)
        
        # Get context second time
        context2 = session_manager.get_context(session_id)
        
        assert context1 is context2
    
    def test_multiple_sessions(self, session_manager):
        """Test managing multiple sessions"""
        session_ids = ["session_1", "session_2", "session_3"]
        
        contexts = {}
        for session_id in session_ids:
            contexts[session_id] = session_manager.get_context(session_id)
        
        assert len(session_manager.conversations) == 3
        
        # Verify each context is unique
        for i, session_id in enumerate(session_ids):
            assert session_manager.conversations[session_id] == contexts[session_id]


class TestCurrentSessionManagement:
    """Test current session tracking"""
    
    def test_set_current_session(self, session_manager):
        """Test setting current session"""
        session_id = "current_session"
        session_manager.set_current_session(session_id)
        
        assert session_manager.current_session_id == session_id
    
    def test_switch_current_session(self, session_manager):
        """Test switching between sessions"""
        session1 = "session_1"
        session2 = "session_2"
        
        session_manager.set_current_session(session1)
        assert session_manager.current_session_id == session1
        
        session_manager.set_current_session(session2)
        assert session_manager.current_session_id == session2


class TestChatHistorySaving:
    """Test chat history persistence"""
    
    def test_save_chat_history_creates_file(self, session_manager):
        """Test save_chat_history creates chat file"""
        session_id = "test_save_session"
        user_message = "Hello, how are you?"
        agent_response = {
            "agent": "fallback",
            "processed": "I'm doing well, thank you!",
            "confidence": 0.9,
            "metadata": {}
        }
        
        session_manager.save_chat_history(session_id, user_message, agent_response)
        
        chat_file = session_manager.prompts_dir / f"chat_history_{session_id}.json"
        assert chat_file.exists()
    
    def test_save_chat_history_content(self, session_manager):
        """Test save_chat_history saves correct content"""
        session_id = "content_test_session"
        user_message = "Test message"
        agent_response = {
            "agent": "symptom",
            "processed": "Test response",
            "confidence": 0.95,
            "metadata": {"key": "value"}
        }
        
        session_manager.save_chat_history(session_id, user_message, agent_response)
        
        chat_file = session_manager.prompts_dir / f"chat_history_{session_id}.json"
        with open(chat_file, 'r') as f:
            data = json.load(f)
        
        assert data["session_id"] == session_id
        assert "started_at" in data
        assert "last_updated" in data
        assert len(data["messages"]) == 1
        
        message = data["messages"][0]
        assert message["user"] == user_message
        assert message["agent"] == "symptom"
        assert message["response"] == "Test response"
        assert message["confidence"] == 0.95
        assert message["metadata"] == {"key": "value"}
    
    def test_save_multiple_messages(self, session_manager):
        """Test saving multiple messages to same session"""
        session_id = "multi_message_session"
        
        messages = [
            ("Message 1", {"agent": "fallback", "processed": "Response 1", "confidence": 0.8, "metadata": {}}),
            ("Message 2", {"agent": "symptom", "processed": "Response 2", "confidence": 0.9, "metadata": {}}),
            ("Message 3", {"agent": "medication", "processed": "Response 3", "confidence": 0.85, "metadata": {}})
        ]
        
        for user_msg, agent_resp in messages:
            session_manager.save_chat_history(session_id, user_msg, agent_resp)
        
        chat_file = session_manager.prompts_dir / f"chat_history_{session_id}.json"
        with open(chat_file, 'r') as f:
            data = json.load(f)
        
        assert len(data["messages"]) == 3
        
        for i, (user_msg, agent_resp) in enumerate(messages):
            assert data["messages"][i]["user"] == user_msg
            assert data["messages"][i]["response"] == agent_resp["processed"]
    
    def test_save_updates_timestamp(self, session_manager):
        """Test that saving updates last_updated timestamp"""
        session_id = "timestamp_session"
        
        # Save first message
        session_manager.save_chat_history(
            session_id,
            "First message",
            {"agent": "fallback", "processed": "First response", "confidence": 0.8, "metadata": {}}
        )
        
        chat_file = session_manager.prompts_dir / f"chat_history_{session_id}.json"
        with open(chat_file, 'r') as f:
            data1 = json.load(f)
        
        first_timestamp = data1["last_updated"]
        
        # Save second message
        session_manager.save_chat_history(
            session_id,
            "Second message",
            {"agent": "symptom", "processed": "Second response", "confidence": 0.9, "metadata": {}}
        )
        
        with open(chat_file, 'r') as f:
            data2 = json.load(f)
        
        second_timestamp = data2["last_updated"]
        
        assert second_timestamp >= first_timestamp
    
    def test_save_preserves_existing_history(self, session_manager):
        """Test that saving new message preserves existing history"""
        session_id = "preserve_session"
        
        # Manually create initial history
        chat_file = session_manager.prompts_dir / f"chat_history_{session_id}.json"
        initial_data = {
            "session_id": session_id,
            "started_at": "2026-01-01T00:00:00Z",
            "messages": [
                {
                    "timestamp": "2026-01-01T00:00:00Z",
                    "user": "Existing message",
                    "agent": "fallback",
                    "response": "Existing response",
                    "confidence": 0.8,
                    "metadata": {}
                }
            ]
        }
        
        with open(chat_file, 'w') as f:
            json.dump(initial_data, f)
        
        # Save new message
        session_manager.save_chat_history(
            session_id,
            "New message",
            {"agent": "symptom", "processed": "New response", "confidence": 0.9, "metadata": {}}
        )
        
        # Verify both messages exist
        with open(chat_file, 'r') as f:
            data = json.load(f)
        
        assert len(data["messages"]) == 2
        assert data["messages"][0]["user"] == "Existing message"
        assert data["messages"][1]["user"] == "New message"
        assert data["started_at"] == "2026-01-01T00:00:00Z"  # Preserved


class TestErrorHandling:
    """Test error handling in SessionManager"""
    
    def test_save_chat_history_handles_permission_error(self, session_manager, monkeypatch):
        """Test graceful handling of file permission errors"""
        def mock_open(*args, **kwargs):
            raise PermissionError("Permission denied")
        
        monkeypatch.setattr("builtins.open", mock_open)
        
        # Should not raise exception
        session_manager.save_chat_history(
            "error_session",
            "Test",
            {"agent": "fallback", "processed": "Test", "confidence": 0.8, "metadata": {}}
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
