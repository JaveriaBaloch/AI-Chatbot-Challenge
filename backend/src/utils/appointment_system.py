"""
Dummy Appointment Booking System
Manages specialist appointments based on medical conditions
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
from pathlib import Path

class AppointmentSystem:
    """Mock appointment booking system for healthcare specialists"""
    
    def __init__(self):
        # Set up data directory paths
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.specialists_file = self.data_dir / "specialists.json"
        self.mapping_file = self.data_dir / "specialist_mapping.json"
        self.appointments_file = self.data_dir / "appointments.json"
        
        # Load specialists and mappings from JSON files
        self.specialists = self._load_specialists()
        self.specialist_map = self._load_specialist_mapping()
    
    def _load_specialists(self) -> Dict:
        """Load specialists from JSON file"""
        try:
            if self.specialists_file.exists():
                with open(self.specialists_file, 'r') as f:
                    data = json.load(f)
                    return data.get("specialists", {})
            return {}
        except Exception as e:
            print(f"Error loading specialists: {e}")
            return {}
    
    def _load_specialist_mapping(self) -> Dict:
        """Load specialist mapping from JSON file"""
        try:
            if self.mapping_file.exists():
                with open(self.mapping_file, 'r') as f:
                    data = json.load(f)
                    return data.get("specialist_mapping", {})
            return {}
        except Exception as e:
            print(f"Error loading specialist mapping: {e}")
            return {}

    
    def get_all_specialist_types(self) -> List[Dict]:
        """Get list of all available specialist types for selection"""
        specialist_list = []
        for specialist_type, info in self.specialists.items():
            if specialist_type != "Emergency Medicine":  # Exclude emergency
                specialist_list.append({
                    "type": specialist_type,
                    "name": info["name"],
                    "specialty": info["specialty"]
                })
        return sorted(specialist_list, key=lambda x: x["specialty"])
    
    def get_specialists_for_condition(self, condition: str) -> List[Dict]:
        """Get recommended specialists based on condition keywords"""
        condition_lower = condition.lower()
        specialists = []
        
        # Check for matching conditions
        for keyword, specialist_types in self.specialist_map.items():
            if keyword in condition_lower:
                for specialist_type in specialist_types:
                    if specialist_type in self.specialists:
                        specialist_info = self.specialists[specialist_type].copy()
                        specialist_info['type'] = specialist_type
                        if specialist_info not in specialists:
                            specialists.append(specialist_info)
        
        # Default to Primary Care if no match
        if not specialists:
            pcp = self.specialists.get("Primary Care Physician", {}).copy()
            if pcp:
                pcp['type'] = "Primary Care Physician"
                specialists.append(pcp)
        
        return specialists
    
    def get_available_slots(self, specialist_type: str, days_ahead: int = 7) -> List[Dict]:
        """Generate available appointment slots for the next N days"""
        slots = []
        start_date = datetime.now() + timedelta(days=1)  # Start from tomorrow
        
        for day in range(days_ahead):
            current_date = start_date + timedelta(days=day)
            
            # Skip weekends for most specialists
            if current_date.weekday() >= 5 and specialist_type != "Emergency Medicine":
                continue
            
            # Generate slots (9 AM to 4 PM, hourly)
            for hour in range(9, 16):
                slot_time = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                slots.append({
                    "datetime": slot_time.isoformat(),
                    "display": slot_time.strftime("%A, %B %d at %I:%M %p"),
                    "available": True
                })
        
        return slots[:10]  # Return first 10 available slots
    
    def _sanitize_reason(self, reason: str) -> str:
        """Extract or generate a concise appointment reason from conversation text"""
        if not reason:
            return "General consultation"
        
        # If reason is very long (likely full AI response), extract key information
        if len(reason) > 200:
            # Look for key medical terms or symptoms in the text
            reason_lower = reason.lower()
            
            # Common medical concerns mapping
            conditions = {
                "chest pain": "Chest pain consultation",
                "headache": "Headache evaluation",
                "stomach cramp": "Stomach cramps and digestive issues",
                "abdominal pain": "Abdominal pain evaluation",
                "fever": "Fever and related symptoms",
                "cough": "Persistent cough evaluation",
                "shortness of breath": "Breathing difficulty assessment",
                "dizziness": "Dizziness and balance issues",
                "fatigue": "Chronic fatigue evaluation",
                "medication": "Medication review and concerns",
                "blood pressure": "Blood pressure management",
                "diabetes": "Diabetes management",
                "anxiety": "Anxiety and mental health consultation",
                "depression": "Depression evaluation",
                "back pain": "Back pain assessment",
                "joint pain": "Joint pain evaluation",
                "skin rash": "Skin condition evaluation",
                "allergy": "Allergy assessment",
                "asthma": "Asthma management"
            }
            
            # Find matching conditions
            for condition, description in conditions.items():
                if condition in reason_lower:
                    return description
            
            # If no specific condition found, look for specialist type in reason
            if "follow" in reason_lower and "up" in reason_lower:
                return "Follow-up consultation"
            
            # Default for unclear reasons
            return "General health consultation"
        
        # If reason is already concise, return it
        return reason.strip()
    
    def book_appointment(self, patient_name: str, specialist_type: str, 
                        slot_datetime: str, reason: str, patient_email: str = None,
                        patient_phone: str = None, reasoning: str = None) -> Dict:
        """Book an appointment"""
        try:
            # Load existing appointments
            if self.appointments_file.exists():
                with open(self.appointments_file, 'r') as f:
                    appointments = json.load(f)
            else:
                appointments = {"appointments": []}
            
            # Sanitize the reason to make it concise
            sanitized_reason = self._sanitize_reason(reason)
            
            # Create new appointment
            appointment = {
                "id": f"APT-{len(appointments['appointments']) + 1:04d}",
                "patient_name": patient_name,
                "patient_email": patient_email,
                "patient_phone": patient_phone,
                "specialist": self.specialists.get(specialist_type, {}),
                "specialist_type": specialist_type,
                "datetime": slot_datetime,
                "reason": sanitized_reason,
                "status": "confirmed",
                "booked_at": datetime.utcnow().isoformat() + "Z"
            }
            
            appointments["appointments"].append(appointment)
            
            # Save appointments
            with open(self.appointments_file, 'w') as f:
                json.dump(appointments, f, indent=2)
            
            # Format the appointment date for display
            try:
                apt_datetime = datetime.fromisoformat(slot_datetime.replace('Z', '+00:00'))
                formatted_date = apt_datetime.strftime("%A, %B %d at %I:%M %p")
            except:
                formatted_date = slot_datetime
            
            confirmation_message = f"""See you on {formatted_date}! 📅

Your appointment with {appointment['specialist'].get('name', specialist_type)} has been confirmed.

Meanwhile, if you have any questions or need to reschedule:
📧 Email us at: support@mamahealth.com
📱 Call us at: +1 (555) 123-4567

We look forward to seeing you!"""
            
            return {
                "success": True,
                "appointment": appointment,
                "message": confirmation_message
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to book appointment"
            }
    
    def get_all_appointments(self) -> List[Dict]:
        """Get all booked appointments"""
        try:
            if self.appointments_file.exists():
                with open(self.appointments_file, 'r') as f:
                    data = json.load(f)
                    return data.get("appointments", [])
            return []
        except Exception as e:
            return []
