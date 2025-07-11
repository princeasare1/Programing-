from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class ClaimResponse(BaseModel):
    id: int
    patient_id: int
    claim_number: str
    status: str
    total_charges: float

@router.get("/claims", response_model=List[ClaimResponse])
async def get_claims():
    """Get claims - placeholder endpoint"""
    return []

@router.post("/claims")
async def create_claim():
    """Create claim - placeholder endpoint"""
    return {"message": "Claim created"}