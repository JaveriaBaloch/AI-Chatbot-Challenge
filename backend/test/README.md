# Test Suite for AI Engineer Challenge Backend

This directory contains comprehensive test cases for the AI Engineer Challenge backend API.

## Test Files

- **test_api.py**: Tests for all API endpoints including message processing, chat management, and appointments
- **test_session_manager.py**: Tests for the SessionManager core component
- **test_appointment_system.py**: Tests for the AppointmentSystem utility

## Setup

Install test dependencies:
```bash
pip install -r requirements.txt
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with verbose output
```bash
pytest -v
```

### Run specific test file
```bash
pytest test/test_api.py
pytest test/test_session_manager.py
pytest test/test_appointment_system.py
```

### Run specific test class
```bash
pytest test/test_api.py::TestRootEndpoints
pytest test/test_api.py::TestMessageProcessing
```

### Run specific test function
```bash
pytest test/test_api.py::TestRootEndpoints::test_health_check
```

### Run with coverage
```bash
pip install pytest-cov
pytest --cov=src --cov-report=html
```

## Test Coverage

### API Endpoints (test_api.py)
- ✅ Root endpoints (/, /api/health)
- ✅ Message processing (/api/process)
- ✅ Chat history (/api/history)
- ✅ Session management (/api/reset, /api/chats/new, /api/chats/list, /api/chats/switch)
- ✅ Appointment operations (get specialists, slots, book, confirm, list)
- ✅ Complete integration flows

### SessionManager (test_session_manager.py)
- ✅ Initialization and setup
- ✅ Context management (get, create, retrieve)
- ✅ Current session tracking
- ✅ Chat history persistence
- ✅ Multiple message handling
- ✅ Error handling

### AppointmentSystem (test_appointment_system.py)
- ✅ Specialist retrieval (condition-based, all types)
- ✅ Slot generation (availability, multiple days)
- ✅ Appointment booking (success, validation)
- ✅ Email and phone validation
- ✅ Data persistence
- ✅ Unique ID generation

## Test Statistics

- **Total Test Cases**: 50+
- **Test Classes**: 15+
- **Coverage Areas**: API endpoints, Core logic, Utilities, Integration flows

## Notes

- Tests use temporary directories to avoid affecting production data
- All tests are isolated and can run independently
- Fixtures handle setup and teardown automatically
- Mock data is used for external dependencies
