from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class LabOrderResponse(BaseModel):
    id: int
    patient_id: int
    order_number: str
    status: str

@router.get("/orders", response_model=List[LabOrderResponse])
async def get_lab_orders():
    """Get lab orders - placeholder endpoint"""
    return []

@router.post("/orders")
async def create_lab_order():
    """Create lab order - placeholder endpoint"""
    return {"message": "Lab order created"}