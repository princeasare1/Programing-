from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class ClinicalNoteResponse(BaseModel):
    id: int
    patient_id: int
    provider_id: int
    note_type: str
    title: str

@router.get("/notes", response_model=List[ClinicalNoteResponse])
async def get_clinical_notes():
    """Get clinical notes - placeholder endpoint"""
    return []

@router.post("/notes", response_model=ClinicalNoteResponse)
async def create_clinical_note():
    """Create clinical note - placeholder endpoint"""
    return ClinicalNoteResponse(
        id=1,
        patient_id=1,
        provider_id=1,
        note_type="SOAP",
        title="Patient Visit"
    )