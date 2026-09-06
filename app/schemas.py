from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any


class ConsultationCreateResponse(BaseModel):
    id: int
    status: str


class SpeakerTurn(BaseModel):
    speaker: str  # "Doctor" | "Patient"
    text: str


class SOAPNote(BaseModel):
    subjective: str
    objective: str
    assessment: str
    plan: str


class ExtractionResult(BaseModel):
    speaker_transcript: List[SpeakerTurn]
    chief_complaint: str
    primary_diagnosis: str
    symptoms: List[str]
    history: str
    medications: List[str]
    investigations: List[str]
    soap: SOAPNote
    action_items: List[str]


class ConsultationStatusResponse(BaseModel):
    id: int
    status: str
    error: Optional[str] = None
    raw_transcript: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class DoctorSignup(BaseModel):
    name: str
    email: EmailStr
    password: str
    specialization: Optional[str] = None


class DoctorLogin(BaseModel):
    email: EmailStr
    password: str


class PatientCreate(BaseModel):
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
