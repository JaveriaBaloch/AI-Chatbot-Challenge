# AI Health Assistant RAG Application

A sophisticated multiagent orchestration system for healthcare that routes patient queries to specialized AI agents (Symptom, Medication, Lifestyle) using Google Gemini Flash, with intelligent appointment booking and conversation management.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.14+
- Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

### Setup

```bash
# Set up environment variables
echo "GEMINI_API_KEY=your_api_key_here" > .env


# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt


# Run tests (50 tests should pass)
pytest test/ -v

# Start server
uvicorn main:app --reload --port 8000
```

**Access Application**:
- **Frontend Chat Interface**: http://localhost:8000/chat
- **Backend API Server**: http://localhost:8000
- **API Health Check**: http://localhost:8000/api/health

---


## 📁 Project Structure

```
backend/
├── src/
│   ├── agents/              # Specialist agents (Symptom, Medication, Lifestyle)
│   ├── orchestrator/        # Router agent and orchestration logic
│   ├── models/              # Pydantic data models
│   ├── core/                # Session management
│   └── utils/               # Appointment system, Gemini client
├── test/                    # 50 comprehensive tests
├── data/                    # Specialist mappings, appointments
│   ├── specialists.json
│   ├── specialist_mapping.json  # Keyword → Specialist mapping
│   └── appointments.json
├── prompts/                 # Chat history JSON files
└── main.py                  # FastAPI application

frontend/public/index.html   # Vanilla JS chat interface
```

---

## 🏗️ Architecture

### Multiagent System Flow

```
User Query → Router Agent (Gemini Flash) → Specialist Agent → Response
                     ↓
              [Symptom | Medication | Lifestyle | Fallback]
                     ↓
              SessionManager (saves to JSON)
                     ↓
              AppointmentSystem (if booking triggered)
```

### Key Components

**1. Router Agent** - Analyzes query intent and routes to appropriate specialist

**2. Specialist Agents** - Domain experts with carefully crafted prompts

**3. Session Manager** - Maintains conversation context (last 5-10 messages)

**4. Appointment System** - Keyword-based specialist matching and booking

---

## 💡 Intelligent Specialist Matching

### How It Works

When users describe symptoms or health concerns, the system uses **keyword-based mapping** to recommend appropriate specialists:

**Specialist Mapping** (`data/specialist_mapping.json`):
```json
{
  "specialist_mapping": {
    "headache": ["Neurologist", "Primary Care Physician"],
    "chest pain": ["Cardiologist", "Emergency Medicine"],
    "stomach pain": ["Gastroenterologist", "Primary Care Physician"],
    "diabetes": ["Endocrinologist", "Primary Care Physician"],
    "pregnancy": ["OB-GYN", "Maternal-Fetal Medicine"]
  }
}
```

### Matching Process

1. **User Query**: "I have persistent headaches and joint pain"
2. **Keyword Detection**: System scans for medical keywords in user message
3. **Specialist Lookup**: 
   - `"headache"` → `["Neurologist", "Primary Care Physician"]`
   - `"joint pain"` → `["Rheumatologist", "Orthopedist"]`
4. **Deduplication**: Combines and removes duplicate specialists
5. **Prioritization**: Emergency specialists ranked first if critical keywords detected
6. **Fallback**: If no keywords match → `["Primary Care Physician"]`

### Example Flow

```
User: "I've been having stomach cramps after taking my medication"

Keyword Detection:
  ✓ "stomach" → Gastroenterologist, Primary Care Physician
  ✓ "medication" → Primary Care Physician

Specialist Recommendations:
  1. Gastroenterologist (for stomach issue)
  2. Primary Care Physician (for both issues)

UI Display:
  Shows both specialists with available time slots
  User selects preferred specialist and books appointment
```

### Benefits

- **Fast Matching**: O(n) keyword lookup, no complex AI inference needed
- **Predictable**: Consistent specialist recommendations for same keywords
- **Maintainable**: Easy to add new keywords or specialists via JSON
- **Multilingual Ready**: Can add keyword translations for i18n support
- **Fallback Safe**: Always recommends Primary Care if no match found

---

## 🔄 Conversation Context Management

### Sliding Window Approach

Agents receive the **last 5-10 messages** from chat history for context:

```python
# Context passed to agents:
context = [
    {"user": "I have a headache", "agent": "symptom"},
    {"user": "It's been 3 days", "agent": "symptom"},
    {"user": "Should I book an appointment?", "agent": "symptom"}
]
# Current: "What specialist should I see?"
# Agent understands context: asking about headache specialist
```

### JSON Storage Strategy

**Why JSON over plain text?**

```json
{
  "session_id": "chat_20260121_094459",
  "messages": [
    {
      "timestamp": "2026-01-21T09:45:00Z",
      "user": "I have a headache",
      "agent": "symptom",
      "response": "...",
      "metadata": {
        "routing": {"target_agent": "symptom", "confidence": 0.95}
      }
    }
  ]
}
```

**Benefits**:
- ✅ **Structured data** for easy parsing and analysis
- ✅ **Training-ready** for future AI model fine-tuning
- ✅ **Analytics** on routing accuracy and agent performance
- ✅ **Scalable** - add new fields without breaking existing data
- ✅ **Queryable** - filter by agent, confidence, timestamps

### Why JSON Over Plain Text?

**JSON chosen for chat storage because**:

1. **Structured Data**: Each message has typed fields (timestamp, agent, metadata) vs. unstructured text
2. **AI Training Ready**: Can export conversations for fine-tuning future models
3. **Analytics**: Track routing accuracy, confidence scores, agent performance over time
4. **Metadata Storage**: Store routing decisions, reasoning, appointment IDs alongside messages
5. **Easy Parsing**: No regex or text parsing needed - direct object access
6. **Backward Compatible**: Add new fields without breaking existing conversation files
7. **Queryable**: Filter by agent type, date range, confidence thresholds
8. **Integration**: Export to databases, analytics tools, or data pipelines

**Example Use Cases**:
- "Show all symptom agent conversations with confidence <0.7" (routing quality check)
- "Export all medication queries for specialist review"
- "Track average response times by agent type"

---

## 🔐 Privacy-First Appointment System

**No user accounts required** - Anonymous chatting with contact collection only at booking:

- **Session-based**: Chat using temporary session IDs
- **Contact at booking**: Email/phone captured only when scheduling appointments
- **Follow-up enabled**: Healthcare providers can reach patients for:
  - Appointment reminders
  - Test results
  - Rescheduling
  - Follow-up care

**Data stored**:
```json
{
  "patient_name": "Jane Doe",
  "patient_email": "jane@example.com",
  "patient_phone": "+1 555-1234",
  "specialist": "Dr. Sarah Johnson (Neurologist)",
  "reason": "Headache evaluation"  // Sanitized from AI response
}
```

---

## 📡 API Documentation

### Base URL
- **Development**: http://localhost:8000
- **Frontend**: http://localhost:8000/chat

### Core Endpoints

#### 1. Health & Status

**GET** `/`
- Returns welcome message

**GET** `/api/health`
- Health check endpoint
- Response:
```json
{
  "status": "healthy",
  "orchestrator_ready": true,
  "env_loaded": true
}
```

---

#### 2. Chat & Message Processing

**POST** `/api/process`
- Process user message through multiagent system
- Request:
```json
{
  "text": "I have a persistent headache",
  "session_id": "chat_20260121_123456_abc123"
}
```
- Response:
```json
{
  "original": "I have a persistent headache",
  "processed": "I am sorry to hear about your headache...",
  "agent": "symptom",
  "confidence": 0.95,
  "timestamp": "2026-01-21T10:30:00Z",
  "metadata": {
    "routing": {
      "target_agent": "symptom",
      "reasoning": "Physical symptom requiring assessment",
      "confidence": 0.95
    }
  }
}
```

**GET** `/api/history?session_id={session_id}`
- Retrieve chat history for session
- Returns JSON with messages array

---

#### 3. Session Management

**POST** `/api/chats/new`
- Create new chat session
- Response:
```json
{
  "status": "success",
  "session_id": "chat_20260121_123456_abc123",
  "message": "New chat created"
}
```

**GET** `/api/chats/list`
- List all chat sessions with metadata
- Response:
```json
{
  "success": true,
  "chats": [
    {
      "session_id": "chat_20260121_123456",
      "started_at": "2026-01-21T10:00:00Z",
      "last_updated": "2026-01-21T10:30:00Z",
      "message_count": 12,
      "preview": "I have a persistent headache...",
      "is_active": true
    }
  ],
  "current_session_id": "chat_20260121_123456"
}
```

**POST** `/api/chats/switch`
- Switch to different session
- Request:
```json
{
  "session_id": "chat_20260120_100000_xyz789"
}
```

**POST** `/api/reset`
- Reset conversation and create new session
- Response: New session details

---

#### 4. Appointment System

**POST** `/api/appointments/get-specialists`
- Get specialists for a condition
- Request:
```json
{
  "condition": "headache"
}
```
- Response:
```json
{
  "success": true,
  "specialists": [
    {
      "name": "Dr. Sarah Johnson",
      "specialty": "Neurologist",
      "available_slots": ["2026-01-22T10:00:00", "2026-01-22T14:30:00"]
    }
  ]
}
```

**GET** `/api/appointments/specialist-types`
- List all available specialist types
- Response:
```json
{
  "success": true,
  "specialists": [
    {"specialty": "Primary Care Physician"},
    {"specialty": "Neurologist"},
    {"specialty": "Cardiologist"},
    {"specialty": "OB-GYN"}
  ]
}
```

**POST** `/api/appointments/get-slots`
- Get available time slots for specialist
- Request:
```json
{
  "specialist_type": "Neurologist"
}
```
- Response:
```json
{
  "success": true,
  "slots": [
    {"datetime": "2026-01-22T09:00:00", "available": true},
    {"datetime": "2026-01-22T09:30:00", "available": true}
  ]
}
```

**POST** `/api/appointments/book`
- Book an appointment
- Request:
```json
{
  "patient_name": "Jane Doe",
  "patient_email": "jane@example.com",
  "patient_phone": "+1 555-1234",
  "specialist_type": "Neurologist",
  "slot_datetime": "2026-01-22T10:00:00",
  "reason": "Persistent headache",
  "reasoning": "Physical symptom requiring specialist assessment"
}
```
- Response:
```json
{
  "success": true,
  "appointment_id": "APT-0001",
  "appointment": {
    "id": "APT-0001",
    "patient_name": "Jane Doe",
    "specialist": "Dr. Sarah Johnson (Neurologist)",
    "datetime": "2026-01-22T10:00:00",
    "reason": "Headache evaluation",
    "status": "confirmed"
  }
}
```

**POST** `/api/appointments/confirm`
- Save appointment confirmation to chat history
- Request:
```json
{
  "session_id": "chat_20260121_123456",
  "message": "Appointment confirmed message",
  "appointment_id": "APT-0001",
  "reasoning": "Physical symptom assessment"
}
```

**GET** `/api/appointments`
- Retrieve all appointments
- Response:
```json
{
  "success": true,
  "appointments": [
    {
      "id": "APT-0001",
      "patient_name": "Jane Doe",
      "specialist": "Dr. Sarah Johnson (Neurologist)",
      "datetime": "2026-01-22T10:00:00"
    }
  ]
}
```

---

#### 5. Frontend

**GET** `/chat`
- Serves the frontend HTML interface
- Access at: http://localhost:8000/chat

---

## 🎯 Prompt Engineering Strategy

### Design Principles

Each agent has carefully crafted prompts focusing on:
- **Clear Boundaries**: Explicit role definitions and scope limitations
- **Safety First**: Emergency triage and appropriate escalation paths
- **Consistency**: Standardized response formats across all agents
- **Actionability**: Appointment booking triggers and next steps

### Router Agent

**Purpose**: Classify intent and delegate to appropriate specialist

```
Routing Logic:
- symptom: Physical pain, discomfort, severity assessment
- medication: Drug questions, dosages, interactions
- lifestyle: Diet, exercise, chronic condition management
- fallback: Greetings, unclear queries

Priority: symptoms > medications > lifestyle (safety-first)
```

**Output**: JSON with `target_agent`, `reasoning`, `confidence`

### Specialist Agent Prompts

#### Symptom Agent

**EXPERTISE**: Physical symptoms, pain assessment, emergency triage, maternal health concerns

**BOUNDARIES**:
- Physical symptoms only (pain, discomfort, changes in body)
- NOT medications, dosages, or lifestyle advice
- Can assess urgency and recommend care level

**APPOINTMENT BOOKING GUIDANCE**:

*WHEN TO RECOMMEND APPOINTMENT BOOKING*:
- Persistent symptoms (lasting >3 days)
- Moderate severity (5-7/10 pain scale)
- Non-emergency but concerning symptoms
- Follow-up needed for existing conditions
- Preventive care or screening needed

*WHEN TO STILL RECOMMEND EMERGENCY CARE*:
- Sudden severe pain (8-10/10)
- Signs of stroke (facial drooping, weakness, slurred speech)
- Chest pain or difficulty breathing
- Heavy bleeding
- Severe allergic reactions
- Loss of consciousness
- Fever >103°F with confusion

**APPOINTMENT RECOMMENDATIONS**:
- Headaches → Neurologist or Primary Care
- Abdominal pain → Gastroenterologist
- Joint pain → Rheumatologist or Orthopedist
- Pregnancy concerns → OB-GYN
- General symptoms → Primary Care Physician

**TONE**: Empathetic, reassuring, safety-focused

**Remember**: *Connect patients to care through appointments when appropriate, not just emergency services.*

---

#### Medication Agent

**EXPERTISE**: Medication information, drug interactions, side effects, dosing guidance (informational only)

**BOUNDARIES**:
- Information ONLY - never prescribe or change dosages
- Explain how medications work
- Identify potential interactions
- Route physical symptoms to Symptom Agent

**APPOINTMENT BOOKING GUIDANCE**:

*WHEN TO RECOMMEND APPOINTMENT BOOKING*:
- Questions about changing current medications
- Concerns about side effects
- Need for medication review
- New medication needed
- Prescription refills

**APPOINTMENT RECOMMENDATIONS**:
- Medication adjustments → Primary Care or Prescribing Specialist
- Side effects → Prescribing Doctor
- Drug interactions → Pharmacist consultation or Primary Care

**TONE**: Clear, factual, cautious

**Remember**: *"Always consult your healthcare provider before changing medications."*

---

#### Lifestyle Agent

**EXPERTISE**: Diet, exercise, stress management, chronic condition management, wellness coaching

**BOUNDARIES**:
- Preventive care and daily management ONLY
- NOT acute symptoms or medications
- Routes new symptoms to Symptom Agent

**APPOINTMENT BOOKING GUIDANCE**:

*WHEN TO RECOMMEND APPOINTMENT BOOKING*:
- Nutrition counseling needed → Registered Dietitian
- Chronic condition management → Endocrinologist, Cardiologist
- Weight management → Nutritionist or Bariatric Specialist
- Exercise prescription → Physical Therapist

**TONE**: Encouraging, practical, evidence-based

**Remember**: *Lifestyle changes work best alongside professional medical care.*

---

### Edge Case Handling

| Scenario | Handling |
|----------|----------|
| Multi-topic (symptom + medication) | Route to symptom agent (safety-first) |
| Vague query ("I don't feel well") | Fallback agent asks clarifying questions |
| Emergency keywords | Route to symptom agent with 911 guidance |
| Out-of-scope | Polite redirect or fallback response |

---

## 🧪 Testing Strategy

Our test suite focuses on **meaningful behavior verification** rather than coverage metrics. We test critical user journeys, edge cases, and integration points.

### Test Categories

#### 1. API Endpoint Tests (`test/test_api.py` - 24 tests)

**Root Endpoints**:
- ✅ Health check returns correct status
- ✅ Root endpoint serves HTML

**Message Processing**:
- ✅ Processes messages without session ID
- ✅ Processes messages with valid session ID
- ✅ Handles invalid payload gracefully
- ✅ Routes symptom-related messages correctly

**Session Management**:
- ✅ Creates new chat sessions with unique IDs
- ✅ Resets conversation state
- ✅ Lists all chat sessions
- ✅ Switches between sessions
- ✅ Handles missing session IDs

**Appointment System**:
- ✅ Gets specialists for medical conditions
- ✅ Lists all specialist types
- ✅ Generates available appointment slots
- ✅ Books appointments with required fields
- ✅ Validates email format
- ✅ Validates phone format
- ✅ Saves appointment confirmations

**Integration Flow**:
- ✅ Complete chat flow (create → message → history)
- ✅ Complete appointment booking flow

#### 2. Session Manager Tests (`test/test_session_manager.py` - 13 tests)

**Initialization**:
- ✅ Creates prompts directory on init
- ✅ Handles missing directories gracefully

**Context Management**:
- ✅ Creates new context for unknown session
- ✅ Returns existing context for known session
- ✅ Manages multiple sessions independently

**Current Session**:
- ✅ Sets and retrieves current session
- ✅ Switches between sessions correctly

**Chat History**:
- ✅ Saves chat history to JSON files
- ✅ Creates files with correct structure
- ✅ Appends messages to existing history
- ✅ Updates timestamps on save
- ✅ Preserves existing messages
- ✅ Handles permission errors gracefully

#### 3. Appointment System Tests (`test/test_appointment_system.py` - 10 tests)

**Initialization**:
- ✅ Loads specialists and mappings on init

**Specialist Retrieval**:
- ✅ Returns specialists for known conditions
- ✅ Returns list of specialist dicts
- ✅ Lists all specialist types

**Appointment Slots**:
- ✅ Generates future appointment slots
- ✅ Returns slots as dictionaries with correct keys

**Appointment Booking**:
- ✅ Books appointments successfully
- ✅ Includes email and phone in appointments
- ✅ Generates unique sequential IDs
- ✅ Sanitizes long AI responses into concise reasons
- ✅ Keeps short reasons unchanged

**Key Test**: Reason Sanitization
```python
def test_book_appointment_sanitizes_long_reason():
    # 449-character AI response
    long_reason = "I am so sorry to hear you are dealing with..."
    
    result = appointment_system.book_appointment(...)
    
    # Sanitized to 35 characters
    assert len(result["appointment"]["reason"]) < 100
    assert "headache" in result["appointment"]["reason"].lower()
```

### Test Utilities

- **Fixtures**: Temporary directories for file operations
- **Mocking**: Minimal mocking, prefer real implementations
- **Cleanup**: Automatic teardown of test data
- **Isolation**: Each test runs independently

### Running Tests

```bash
# Run all tests with verbose output
pytest test/ -v

# Run specific test file
pytest test/test_api.py -v

# Run with coverage (if coverage installed)
pytest test/ --cov=src --cov-report=html

# Expected output: 50 passed, 105 warnings in ~40s
```

---

## Example Conversations

### Example 1: Symptom Assessment with Emergency Triage

**User**: "I have a headache that won't go away"

**Router Decision**:
```json
{
  "target_agent": "symptom",
  "reasoning": "Query describes a specific symptom (persistent headache) requiring assessment",
  "confidence": 1.0
}
```

**Symptom Agent Response**:
> I am so sorry to hear you are dealing with a headache that won't go away. Persistent headaches can be very disruptive and need proper evaluation.
>
> To help me understand the urgency of the situation, could you tell me a bit more about the headache?
>
> 1. **Duration:** How long has this headache persisted (hours, days, weeks)?
> 2. **Severity:** On a scale of 1 to 10, how painful is it?
> 3. **Accompanying Symptoms:** Are you experiencing vision changes, numbness, confusion, fever, or vomiting?
>
> **Important Note on Urgency:**
> If this headache came on **suddenly and severely** (worst headache of your life), or if you are experiencing **signs of stroke** (facial drooping, weakness, difficulty speaking), please call 911 immediately.
>
> For persistent, non-emergency headaches, I recommend booking an appointment with a **Neurologist** to evaluate this properly.

**Outcome**: Appointment booked with Dr. Sarah Johnson (Neurologist) for January 22 at 12:00 PM

---

### Example 2: Medication Question with Interaction Check

**User**: "Can I take ibuprofen while pregnant?"

**Router Decision**:
```json
{
  "target_agent": "medication",
  "reasoning": "Query about medication safety and usage",
  "confidence": 0.95
}
```

**Medication Agent Response**:
> That's an excellent question, and I'm glad you're being cautious about medication during pregnancy.
>
> **Ibuprofen During Pregnancy:**
> Ibuprofen is generally **not recommended** during pregnancy, especially in the third trimester, as it can:
> - Affect fetal heart development
> - Reduce amniotic fluid levels
> - Potentially delay labor
>
> **Safer Alternatives:**
> - **Acetaminophen (Tylenol)** is typically considered safe during pregnancy for pain relief
> - Always at the lowest effective dose
>
> **Important:** Before taking any medication during pregnancy, please consult with your healthcare provider. They can assess your specific situation and recommend the safest option for you and your baby.

**Agent Behavior**: Provided evidence-based guidance, suggested safer alternative, emphasized provider consultation

---

### Example 3: Multi-Topic Query (Symptom + Medication)

**User**: "I've been having stomach cramps after taking my medication. Should I be worried?"

**Router Decision**:
```json
{
  "target_agent": "symptom",
  "reasoning": "Query mentions both symptoms and medication, but safety-first routing prioritizes the physical symptom assessment",
  "confidence": 0.92
}
```

**Symptom Agent Response**:
> I hear how uncomfortable stomach cramps can be, especially when they coincide with your medication schedule. This is definitely worth investigating.
>
> To better understand what's happening, could you tell me:
>
> 1. **Which medication** are you taking?
> 2. **When do the cramps occur** - immediately after taking it, or hours later?
> 3. **Severity** - are the cramps mild discomfort or sharp pain?
> 4. **Other symptoms** - any nausea, diarrhea, or bloating?
>
> **When to Seek Immediate Care:**
> If the pain is severe, accompanied by fever, blood in stool, or persistent vomiting, please contact your healthcare provider immediately.
>
> In many cases, stomach cramps can be related to medication timing or interactions with food. A **Gastroenterologist** can help evaluate this, and your prescribing physician should also be informed to potentially adjust your medication regimen.

**Agent Behavior**: 
- Router correctly prioritized symptom over medication
- Agent gathered context about both symptom and medication
- Provided appropriate specialist recommendation
- Clear escalation criteria for emergencies

---

### Example 4: Lifestyle Guidance for Chronic Condition

**User**: "What foods should I avoid with gestational diabetes?"

**Router Decision**:
```json
{
  "target_agent": "lifestyle",
  "reasoning": "Query about dietary management for chronic condition",
  "confidence": 0.98
}
```

**Lifestyle Agent Response**:
> Managing gestational diabetes through diet is one of the most important steps you can take for you and your baby's health. Here's what you should know:
>
> **Foods to Limit or Avoid:**
> - **Refined carbohydrates**: White bread, white rice, pastries
> - **Sugary drinks**: Soda, fruit juice, sweetened beverages
> - **High-sugar foods**: Candy, cookies, cake
> - **Processed foods**: Often high in hidden sugars
>
> **Foods to Emphasize:**
> - **Complex carbohydrates**: Whole grain bread, brown rice, quinoa
> - **Lean proteins**: Chicken, fish, tofu, beans
> - **Non-starchy vegetables**: Leafy greens, broccoli, peppers
> - **Healthy fats**: Avocado, nuts, olive oil
>
> **Key Strategies:**
> - Eat smaller, more frequent meals (5-6 per day)
> - Pair carbohydrates with protein to stabilize blood sugar
> - Monitor portion sizes
> - Keep a food diary to track blood sugar responses
>
> **Important:** Work with a registered dietitian who specializes in gestational diabetes for a personalized meal plan. Your healthcare provider can also help you understand target blood sugar ranges.

**Agent Behavior**: Provided actionable, evidence-based dietary guidance with escalation to specialist (dietitian)

---

### Example 5: Ambiguous Query Handling

**User**: "I don't feel well"

**Router Decision**:
```json
{
  "target_agent": "fallback",
  "reasoning": "Query is too vague to determine specific concern",
  "confidence": 0.60
}
```

**Fallback Agent Response**:
> I'm sorry to hear you're not feeling well. To help you most effectively, could you tell me a bit more about what you're experiencing?
>
> For example:
> - Do you have any **physical symptoms** (pain, nausea, headache)?
> - Are you concerned about a **medication** you're taking?
> - Are you looking for **lifestyle advice** on managing a condition?
>
> The more specific you can be, the better I can assist you.

**Agent Behavior**: Politely asks clarifying questions to route to appropriate specialist

---

### Example 6: Appointment Booking Flow

**User Initial Query**: "I have persistent back pain for 3 weeks"

**System Response**: Symptom Agent assesses, recommends Orthopedic Specialist

**User Action**: Clicks "Book Appointment" button

**Appointment System**:
1. Shows available specialists:
   - Dr. Michael Chen (Orthopedic Surgery)
   - Dr. Lisa Anderson (Physical Medicine)
2. User selects specialist
3. Shows available slots (next 7 days, excluding weekends)
4. User selects: Thursday, January 23 at 10:00 AM
5. User enters contact info:
   - Email: patient@example.com
   - Phone: +1 (555) 123-4567

**Confirmation Message**:
> ✅ **Appointment Confirmed!**
>
> **See you on Thursday, January 23 at 10:00 AM!** 📅
>
> Your appointment with **Dr. Michael Chen** has been confirmed.
>
> **Appointment ID:** APT-0002
>

**Saved Data** (`appointments.json`):
```json
{
  "id": "APT-0002",
  "patient_name": "Jane Doe",
  "patient_email": "patient@example.com",
  "patient_phone": "+1 (555) 123-4567",
  "specialist": {
    "name": "Dr. Michael Chen",
    "specialty": "Orthopedic Surgery"
  },
  "datetime": "2026-01-23T10:00:00",
  "reason": "Back pain assessment",
  "status": "confirmed"
}
```

**Chat History** (`prompts/chat_*.json`):
```json
{
  "timestamp": "2026-01-21T10:30:00Z",
  "user": "[Appointment APT-0002 booked]",
  "agent": "system",
  "response": "✅ Appointment Confirmed! ...",
  "metadata": {
    "appointment_id": "APT-0002",
    "type": "appointment_confirmation",
    "reasoning": "The query describes persistent physical pain (back pain) requiring professional assessment"
  }
}
```

---

## Implementation Highlights

### What Makes This System Robust

1. **Safety-First Routing**: Symptoms always prioritized over other topics in multi-concern queries
2. **Context Preservation**: Full conversation history maintained across messages
3. **Data Validation**: Pydantic models ensure type safety throughout
4. **Graceful Degradation**: System handles API failures with user-friendly messages
5. **Appointment Intelligence**: Sanitizes verbose AI responses into concise medical reasons
6. **Multi-Session Support**: Users can switch between different conversation threads
7. **Comprehensive Testing**: 50 tests covering happy paths and edge cases

### Future Enhancements

- **Agent Handoffs**: Explicit mid-conversation transfers between agents
- **Streaming Responses**: Real-time progressive message delivery
- **Voice Input**: Speech-to-text for accessibility
- **Multi-Language**: Support for Spanish, French, etc.
- **Analytics Dashboard**: Track routing accuracy and user satisfaction
- **Emergency Detection**: Automated escalation for critical keywords

---
# AI-Chatbot-Challenge
# AI-Chatbot-Challenge
