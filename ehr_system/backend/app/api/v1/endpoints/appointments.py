from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    provider_id: int
    appointment_date: str
    status: str

@router.get("/", response_model=List[AppointmentResponse])
async def get_appointments():
    """Get appointments - placeholder endpoint"""
    return []

@router.post("/", response_model=AppointmentResponse)
async def create_appointment():
    """Create appointment - placeholder endpoint"""
    return AppointmentResponse(
        id=1,
        patient_id=1,
        provider_id=1,
        appointment_date="2024-01-01T10:00:00",
        status="Scheduled"
    )