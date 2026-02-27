# Data Directory

This directory contains configuration and data files for the AI Health Assistant application.

## Files

### `specialists.json`
Contains information about all available medical specialists including:
- Specialist names
- Specialties
- Hospital/clinic locations
- Availability schedules

### `specialist_mapping.json`
Maps health conditions, symptoms, and keywords to appropriate specialist types. Used by the appointment system to recommend the right specialist for each health concern.

### `appointments.json`
Stores all booked appointments. This file is created automatically when the first appointment is booked.

**Structure:**
```json
{
  "appointments": [
    {
      "id": "APT-0001",
      "patient_name": "Patient Name",
      "specialist": {...},
      "specialist_type": "Cardiologist",
      "datetime": "2026-01-22T10:00:00",
      "reason": "Blood pressure concerns",
      "status": "confirmed",
      "booked_at": "2026-01-21T14:30:00Z"
    }
  ]
}
```

## Usage

These files are automatically loaded by the `AppointmentSystem` class. To modify specialists or mappings, edit the respective JSON files directly.
