from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.models.conversation_context import ConversationContext
from src.models.message_model import MessageModel
from src.orchestrator.orchestrator import AgentOrchestrator
from src.core.session_manager import SessionManager
from src.utils.appointment_system import AppointmentSystem
from datetime import datetime
import os
import logging
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Engineer Challenge API")

# Configure CORS - Must be before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods including OPTIONS
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"]
)

# Initialize orchestrator
try:
    # Check if API key exists
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment variables")
        orchestrator = None
    else:
        logger.info(f"Found GEMINI_API_KEY: {api_key[:10]}...")
        orchestrator = AgentOrchestrator()
        logger.info("Orchestrator initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize orchestrator: {e}", exc_info=True)
    orchestrator = None

# Initialize session manager
PROMPTS_DIR = Path(__file__).parent / "prompts"
session_manager = SessionManager(PROMPTS_DIR)

# Initialize appointment system
appointment_system = AppointmentSystem()

@app.get("/")
async def root():
    return {"message": "Welcome to AI Engineer Challenge API"}

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "orchestrator_ready": orchestrator is not None,
        "env_loaded": os.getenv("GEMINI_API_KEY") is not None
    }

@app.post("/api/process")
async def process_message(message: MessageModel):
    """Process user message through the agent orchestrator"""
    try:
        if not orchestrator:
            raise Exception("Orchestrator not initialized. Check API key configuration.")
        
        # Get or create conversation context
        session_id = message.session_id if hasattr(message, 'session_id') and message.session_id else session_manager.current_session_id or "default"
        
        # Update current session if message has session_id
        if message.session_id:
            session_manager.set_current_session(message.session_id)
        
        context = session_manager.get_context(session_id)
        
        logger.info(f"Processing query: {message.text}")
        
        # Process query through orchestrator
        response = await orchestrator.process_query(message.text, context)
        
        logger.info(f"Response from {response.agent_type.value} agent")
        
        # Update context
        context = orchestrator.update_context(context, message.text, response)
        session_manager.conversations[session_id] = context
        
        response_data = {
            "original": message.text,
            "processed": response.content,
            "agent": response.agent_type.value,
            "confidence": response.confidence,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": response.metadata
        }
        
        # Save chat history to prompts directory
        session_manager.save_chat_history(session_id, message.text, response_data)
        
        return response_data
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        return {
            "original": message.text,
            "processed": f"Sorry, I encountered an error: {str(e)}. Please ensure the API key is configured correctly.",
            "agent": "error",
            "confidence": 0.0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": {"error": str(e)}
        }

@app.get("/api/history")
async def get_chat_history(session_id: str = None):
    """Get chat history for a specific session"""
    try:
        if not session_id:
            session_id = session_manager.current_session_id or "default"
        
        chat_file = PROMPTS_DIR / f"chat_history_{session_id}.json"
        
        if not chat_file.exists():
            return {"messages": [], "session_id": session_id}
        
        with open(chat_file, 'r') as f:
            history = json.load(f)
        
        return history
    except Exception as e:
        logger.error(f"Failed to load chat history: {e}")
        return {"messages": [], "session_id": session_id}

@app.post("/api/reset")
async def reset_conversation():
    """Reset the current conversation context"""
    try:
        # Create a new session
        import uuid
        session_id = f"chat_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        session_manager.set_current_session(session_id)
        
        # Create new conversation context
        session_manager.get_context(session_id)
        
        return {
            "status": "success",
            "session_id": session_id,
            "message": "Conversation reset successfully"
        }
    except Exception as e:
        logger.error(f"Failed to reset conversation: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/chats/new")
async def create_new_chat():
    """Create a new chat session"""
    # Generate unique session ID
    import uuid
    session_id = f"chat_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    session_manager.set_current_session(session_id)
    
    # Create new conversation context
    session_manager.get_context(session_id)
    
    return {
        "status": "success",
        "session_id": session_id,
        "message": "New chat created"
    }

@app.get("/api/chats/list")
async def list_all_chats():
    """List all chat sessions"""
    try:
        chat_files = list(PROMPTS_DIR.glob("chat_history_*.json"))
        chats = []
        
        for chat_file in chat_files:
            try:
                with open(chat_file, 'r') as f:
                    data = json.load(f)
                    session_id = data.get("session_id", chat_file.stem.replace("chat_history_", ""))
                    
                    # Get first user message as preview
                    preview = "No messages"
                    if data.get("messages") and len(data["messages"]) > 0:
                        first_msg = data["messages"][0]
                        preview = first_msg.get("user", "No message")[:100]
                    
                    chats.append({
                        "session_id": session_id,
                        "started_at": data.get("started_at", ""),
                        "last_updated": data.get("last_updated", ""),
                        "message_count": len(data.get("messages", [])),
                        "preview": preview,
                        "is_active": session_id == session_manager.current_session_id
                    })
            except Exception as e:
                logger.error(f"Error reading chat file {chat_file}: {e}")
                continue
        
        # Sort by last_updated descending
        chats.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
        
        return {
            "success": True,
            "chats": chats,
            "current_session_id": session_manager.current_session_id
        }
    except Exception as e:
        logger.error(f"Failed to list chats: {e}")
        return {
            "success": False,
            "chats": [],
            "error": str(e)
        }

@app.post("/api/chats/switch")
async def switch_chat(data: dict):
    """Switch to a different chat session (read-only for archived chats)"""
    session_id = data.get("session_id")
    
    if not session_id:
        return {"success": False, "error": "session_id required"}
    
    session_manager.set_current_session(session_id)
    
    # Load conversation context if exists
    session_manager.get_context(session_id)
    
    return {
        "success": True,
        "session_id": session_id,
        "message": "Switched to chat session"
    }

@app.post("/api/appointments/get-specialists")
async def get_specialists(data: dict):
    """Get recommended specialists based on condition"""
    try:
        condition = data.get("condition", "")
        specialists = appointment_system.get_specialists_for_condition(condition)
        return {
            "success": True,
            "specialists": specialists
        }
    except Exception as e:
        logger.error(f"Failed to get specialists: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/appointments/specialist-types")
async def get_all_specialist_types():
    """Get all available specialist types for manual selection"""
    try:
        specialists = appointment_system.get_all_specialist_types()
        return {
            "success": True,
            "specialists": specialists
        }
    except Exception as e:
        logger.error(f"Failed to get specialist types: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/appointments/get-slots")
async def get_appointment_slots(data: dict):
    """Get available appointment slots for a specialist"""
    try:
        specialist_type = data.get("specialist_type", "Primary Care Physician")
        slots = appointment_system.get_available_slots(specialist_type)
        return {
            "success": True,
            "slots": slots
        }
    except Exception as e:
        logger.error(f"Failed to get slots: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/appointments/book")
async def book_appointment(data: dict):
    """Book an appointment"""
    try:
        patient_name = data.get("patient_name", "Patient")
        patient_email = data.get("patient_email")
        patient_phone = data.get("patient_phone")
        specialist_type = data.get("specialist_type")
        slot_datetime = data.get("slot_datetime")
        reason = data.get("reason", "General consultation")
        reasoning = data.get("reasoning", "")  # Medical reasoning from routing
        
        result = appointment_system.book_appointment(
            patient_name=patient_name,
            patient_email=patient_email,
            patient_phone=patient_phone,
            specialist_type=specialist_type,
            slot_datetime=slot_datetime,
            reason=reason,
            reasoning=reasoning
        )
        return result
    except Exception as e:
        logger.error(f"Failed to book appointment: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/appointments/confirm")
async def save_appointment_confirmation(data: dict):
    """Save appointment confirmation message to chat history"""
    try:
        session_id = data.get("session_id", "default")
        message = data.get("message", "")
        appointment_id = data.get("appointment_id", "")
        reasoning = data.get("reasoning", "")  # Medical reasoning from routing
        
        # Prepare metadata with reasoning if available
        metadata = {
            "appointment_id": appointment_id,
            "type": "appointment_confirmation"
        }
        if reasoning:
            metadata["reasoning"] = reasoning
        
        # Save to chat history
        response_data = {
            "original": f"[Appointment {appointment_id} booked]",
            "processed": message,
            "agent": "system",
            "confidence": 1.0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": metadata
        }
        
        session_manager.save_chat_history(session_id, f"[Appointment {appointment_id} booked]", response_data)
        
        return {"success": True, "message": "Confirmation saved"}
    except Exception as e:
        logger.error(f"Failed to save confirmation: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/appointments")
async def get_appointments():
    """Get all appointments"""
    try:
        appointments = appointment_system.get_all_appointments()
        return {
            "success": True,
            "appointments": appointments
        }
    except Exception as e:
        logger.error(f"Failed to get appointments: {e}")
        return {
            "success": False,
            "error": str(e),
            "appointments": []
        }

# Serve frontend (optional - add this at the end of the file)
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "public")
if os.path.exists(frontend_path):
    @app.get("/chat")
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_path, "index.html"))
