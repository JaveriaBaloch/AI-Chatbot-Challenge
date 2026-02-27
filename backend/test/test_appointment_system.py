"""
Test cases for AppointmentSystem
"""
import pytest
from datetime import datetime
import json
from pathlib import Path
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.appointment_system import AppointmentSystem


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory with test data"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create specialists.json
    specialists = [
        {
            "name": "Dr. Test Cardiologist",
            "specialty": "Cardiologist",
            "hospital": "Test Hospital",
            "availability": ["Monday", "Wednesday", "Friday"]
        },
        {
            "name": "Dr. Test Neurologist",
            "specialty": "Neurologist",
            "hospital": "Test Clinic",
            "availability": ["Tuesday", "Thursday"]
        }
    ]
    
    with open(data_dir / "specialists.json", 'w') as f:
        json.dump(specialists, f)
    
    # Create specialist_mapping.json
    mapping = {
        "headache": "Neurologist",
        "chest pain": "Cardiologist",
        "heart": "Cardiologist"
    }
    
    with open(data_dir / "specialist_mapping.json", 'w') as f:
        json.dump(mapping, f)
    
    # Create appointments.json
    with open(data_dir / "appointments.json", 'w') as f:
        json.dump([], f)
    
    yield data_dir


@pytest.fixture
def appointment_system():
    """Create AppointmentSystem with production data"""
    # Just use the regular AppointmentSystem which loads from backend/data
    return AppointmentSystem()


class TestAppointmentSystemInitialization:
    """Test AppointmentSystem initialization"""
    
    def test_initialization_loads_data(self, appointment_system):
        """Test that initialization loads data correctly"""
        assert len(appointment_system.specialists) > 0
        assert len(appointment_system.specialist_map) > 0


class TestSpecialistRetrieval:
    """Test specialist retrieval methods"""
    
    def test_get_specialists_for_condition(self, appointment_system):
        """Test getting specialists for condition"""
        specialists = appointment_system.get_specialists_for_condition("headache")
        assert len(specialists) > 0
        assert isinstance(specialists, list)
    
    def test_get_specialists_returns_list(self, appointment_system):
        """Test specialists returned as list"""
        specialists = appointment_system.get_specialists_for_condition("any condition")
        assert isinstance(specialists, list)
    
    def test_get_all_specialist_types(self, appointment_system):
        """Test getting all specialist types"""
        specialists = appointment_system.get_all_specialist_types()
        assert len(specialists) > 0
        
        # Verify structure
        specialist = specialists[0]
        assert "type" in specialist
        assert "name" in specialist
        assert "specialty" in specialist


class TestAppointmentSlots:
    """Test appointment slot generation"""
    
    def test_get_available_slots(self, appointment_system):
        """Test getting available slots for specialist"""
        slots = appointment_system.get_available_slots("Cardiologist")
        assert len(slots) > 0
        assert isinstance(slots, list)
    
    def test_get_available_slots_returns_dicts(self, appointment_system):
        """Test slots are returned as dictionaries with datetime info"""
        slots = appointment_system.get_available_slots("Cardiologist")
        assert all(isinstance(slot, dict) for slot in slots)
        
        # Verify slot structure
        if slots:
            slot = slots[0]
            assert "datetime" in slot
            assert "display" in slot
            assert "available" in slot


class TestAppointmentBooking:
    """Test appointment booking functionality"""
    
    def test_book_appointment_success(self, appointment_system):
        """Test successful appointment booking"""
        result = appointment_system.book_appointment(
            patient_name="John Doe",
            patient_email="john@example.com",
            patient_phone="+1234567890",
            specialist_type="Cardiologist",
            slot_datetime="2026-01-25T10:00:00",
            reason="Chest pain consultation"
        )
        
        assert result["success"] is True
        assert "appointment" in result
        assert "id" in result["appointment"]
        assert "message" in result
    
    def test_book_appointment_includes_contact_info(self, appointment_system):
        """Test appointment includes patient contact information"""
        result = appointment_system.book_appointment(
            patient_name="Jane Smith",
            patient_email="jane@example.com",
            patient_phone="+1987654321",
            specialist_type="Neurologist",
            slot_datetime="2026-01-26T14:00:00",
            reason="Follow-up"
        )
        
        assert result["success"] is True
        appointment = result["appointment"]
        
        # Verify contact information is saved
        assert appointment["patient_email"] == "jane@example.com"
        assert appointment["patient_phone"] == "+1987654321"
        assert appointment["patient_name"] == "Jane Smith"
    
    def test_book_appointment_generates_unique_ids(self, appointment_system):
        """Test that each booking generates unique appointment ID"""
        ids = set()
        
        for i in range(3):
            result = appointment_system.book_appointment(
                patient_name=f"Patient {i}",
                patient_email=f"patient{i}@example.com",
                patient_phone=f"+123456789{i}",
                specialist_type="Cardiologist",
                slot_datetime="2026-01-25T10:00:00",
                reason="Test"
            )
            ids.add(result["appointment"]["id"])
        
        assert len(ids) == 3  # All unique
    
    def test_book_appointment_sanitizes_long_reason(self, appointment_system):
        """Test that long AI responses are sanitized to concise reasons"""
        long_reason = """I hear how uncomfortable and concerning it must be to experience stomach cramps right after taking medication. It is understandable that you would be worried.

To help me understand the severity and pattern of these cramps, could you tell me a little more?

Severity: On a scale of 1 (mild) to 10 (agonizing), how painful are these cramps?"""
        
        result = appointment_system.book_appointment(
            patient_name="Test Patient",
            patient_email="test@example.com",
            patient_phone="+1234567890",
            specialist_type="Gastroenterologist",
            slot_datetime="2026-01-25T10:00:00",
            reason=long_reason
        )
        
        assert result["success"] is True
        # Reason should be sanitized to something concise
        assert len(result["appointment"]["reason"]) < 100
        assert "stomach cramp" in result["appointment"]["reason"].lower() or "digestive" in result["appointment"]["reason"].lower()
    
    def test_book_appointment_keeps_short_reason(self, appointment_system):
        """Test that short, clear reasons are kept as-is"""
        short_reason = "Follow-up consultation"
        
        result = appointment_system.book_appointment(
            patient_name="Test Patient",
            patient_email="test@example.com",
            patient_phone="+1234567890",
            specialist_type="Cardiologist",
            slot_datetime="2026-01-25T10:00:00",
            reason=short_reason
        )
        
        assert result["success"] is True
        assert result["appointment"]["reason"] == short_reason


class TestGetAllAppointments:
    """Test retrieving all appointments"""
    
    def test_get_all_appointments(self, appointment_system):
        """Test getting all appointments"""
        appointments = appointment_system.get_all_appointments()
        assert isinstance(appointments, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
