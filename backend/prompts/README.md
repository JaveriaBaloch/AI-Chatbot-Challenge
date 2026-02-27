# Chat History Storage

This directory stores conversation histories from the AI Health Assistant.

## File Format

Each chat session is stored as a JSON file with the following structure:

```json
{
  "session_id": "default",
  "started_at": "2026-01-21T12:00:00Z",
  "last_updated": "2026-01-21T12:05:00Z",
  "messages": [
    {
      "timestamp": "2026-01-21T12:00:00Z",
      "user": "User's question",
      "agent": "symptom|medication|lifestyle|fallback",
      "response": "Agent's response",
      "confidence": 0.95,
      "metadata": {}
    }
  ]
}
```

## Features

- **Automatic Storage**: Every chat interaction is automatically saved
- **Session-Based**: Each session has its own file (`chat_history_{session_id}.json`)
- **Complete History**: Includes user queries, agent responses, timestamps, and metadata
- **Reset Support**: Chat history is cleared when conversation is reset

## Usage

Chat histories are automatically saved. No manual intervention required.

To view a chat history, open the corresponding JSON file in this directory.
