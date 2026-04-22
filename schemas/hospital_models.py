from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Doctor(BaseModel):
    id: str
    name: str
    specialty: str
    title: str  # e.g. Chief Physician, Attending Physician
    hospital: str
    available_days: str  # e.g. "Mon,Wed,Fri"
    available_times: str  # e.g. "09:00-12:00,14:00-17:00"
    consultation_fee: float


class Patient(BaseModel):
    id: str
    name: str
    date_of_birth: str
    gender: str
    phone: str
    id_number: str  # masked


class Appointment(BaseModel):
    id: str
    patient_id: str
    doctor_id: str
    appointment_date: str  # YYYY-MM-DD
    appointment_time: str  # HH:MM
    status: str  # scheduled / completed / cancelled
    reason: str
    created_at: datetime
    notes: Optional[str] = None
