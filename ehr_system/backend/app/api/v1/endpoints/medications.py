from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class MedicationResponse(BaseModel):
    id: int
    drug_name: str
    generic_name: str
    strength: str

@router.get("/", response_model=List[MedicationResponse])
async def get_medications():
    """Get medications - placeholder endpoint"""
    return []

@router.post("/prescriptions")
async def create_prescription():
    """Create prescription - placeholder endpoint"""
    return {"message": "Prescription created"}