from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import date, datetime
import logging

from ...auth.security import get_current_active_user
from ...database import get_db
from ...models.user import User
from ...models.patient import Patient, InsurancePolicy, VitalSigns, GenderEnum, MaritalStatusEnum, BloodTypeEnum

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models
class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    date_of_birth: date
    gender: GenderEnum
    ssn: Optional[str] = None
    phone_mobile: Optional[str] = None
    email: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    phone_mobile: Optional[str] = None
    email: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class PatientResponse(BaseModel):
    id: int
    patient_id: str
    first_name: str
    last_name: str
    middle_name: Optional[str]
    date_of_birth: date
    gender: GenderEnum
    age: int
    phone_mobile: Optional[str]
    email: Optional[str]
    full_address: str
    patient_status: str
    registration_date: date
    
    class Config:
        from_attributes = True


class PatientSearchResponse(BaseModel):
    total: int
    patients: List[PatientResponse]


class VitalSignsCreate(BaseModel):
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    heart_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    temperature: Optional[float] = None
    oxygen_saturation: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    pain_scale: Optional[int] = None
    notes: Optional[str] = None


class VitalSignsResponse(BaseModel):
    id: int
    recorded_at: datetime
    systolic_bp: Optional[int]
    diastolic_bp: Optional[int]
    heart_rate: Optional[int]
    respiratory_rate: Optional[int]
    temperature: Optional[float]
    oxygen_saturation: Optional[int]
    height: Optional[float]
    weight: Optional[float]
    bmi: Optional[float]
    pain_scale: Optional[int]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


@router.post("/", response_model=PatientResponse)
async def create_patient(
    patient_data: PatientCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new patient"""
    try:
        # Generate unique patient ID (MRN)
        patient_id = f"P{int(datetime.utcnow().timestamp())}"
        
        # Create patient
        patient = Patient(
            patient_id=patient_id,
            first_name=patient_data.first_name,
            last_name=patient_data.last_name,
            middle_name=patient_data.middle_name,
            date_of_birth=patient_data.date_of_birth,
            gender=patient_data.gender,
            ssn=patient_data.ssn,
            phone_mobile=patient_data.phone_mobile,
            email=patient_data.email,
            address_line1=patient_data.address_line1,
            address_line2=patient_data.address_line2,
            city=patient_data.city,
            state=patient_data.state,
            zip_code=patient_data.zip_code,
            emergency_contact_name=patient_data.emergency_contact_name,
            emergency_contact_phone=patient_data.emergency_contact_phone,
            created_by_id=current_user.id,
            registration_date=date.today()
        )
        
        db.add(patient)
        await db.commit()
        await db.refresh(patient)
        
        logger.info(f"Patient {patient.patient_id} created by {current_user.username}")
        
        return PatientResponse(
            id=patient.id,
            patient_id=patient.patient_id,
            first_name=patient.first_name,
            last_name=patient.last_name,
            middle_name=patient.middle_name,
            date_of_birth=patient.date_of_birth,
            gender=patient.gender,
            age=patient.age,
            phone_mobile=patient.phone_mobile,
            email=patient.email,
            full_address=patient.full_address,
            patient_status=patient.patient_status,
            registration_date=patient.registration_date
        )
        
    except Exception as e:
        logger.error(f"Create patient error: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create patient"
        )


@router.get("/search", response_model=PatientSearchResponse)
async def search_patients(
    q: Optional[str] = Query(None, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Search patients"""
    try:
        # Build query
        query = select(Patient).where(Patient.is_active == True)
        
        if q:
            search_filter = or_(
                Patient.first_name.ilike(f"%{q}%"),
                Patient.last_name.ilike(f"%{q}%"),
                Patient.patient_id.ilike(f"%{q}%"),
                Patient.email.ilike(f"%{q}%"),
                Patient.phone_mobile.ilike(f"%{q}%")
            )
            query = query.where(search_filter)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get patients
        query = query.offset(skip).limit(limit).order_by(Patient.last_name, Patient.first_name)
        result = await db.execute(query)
        patients = result.scalars().all()
        
        # Convert to response format
        patient_responses = []
        for patient in patients:
            patient_responses.append(PatientResponse(
                id=patient.id,
                patient_id=patient.patient_id,
                first_name=patient.first_name,
                last_name=patient.last_name,
                middle_name=patient.middle_name,
                date_of_birth=patient.date_of_birth,
                gender=patient.gender,
                age=patient.age,
                phone_mobile=patient.phone_mobile,
                email=patient.email,
                full_address=patient.full_address,
                patient_status=patient.patient_status,
                registration_date=patient.registration_date
            ))
        
        return PatientSearchResponse(
            total=total,
            patients=patient_responses
        )
        
    except Exception as e:
        logger.error(f"Search patients error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not search patients"
        )


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get patient by ID"""
    try:
        # Get patient
        stmt = select(Patient).where(Patient.id == patient_id)
        result = await db.execute(stmt)
        patient = result.scalar_one_or_none()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        return PatientResponse(
            id=patient.id,
            patient_id=patient.patient_id,
            first_name=patient.first_name,
            last_name=patient.last_name,
            middle_name=patient.middle_name,
            date_of_birth=patient.date_of_birth,
            gender=patient.gender,
            age=patient.age,
            phone_mobile=patient.phone_mobile,
            email=patient.email,
            full_address=patient.full_address,
            patient_status=patient.patient_status,
            registration_date=patient.registration_date
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get patient error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve patient"
        )


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update patient information"""
    try:
        # Get patient
        stmt = select(Patient).where(Patient.id == patient_id)
        result = await db.execute(stmt)
        patient = result.scalar_one_or_none()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        # Update fields
        update_data = patient_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(patient, field, value)
        
        patient.updated_by = current_user.username
        
        await db.commit()
        await db.refresh(patient)
        
        logger.info(f"Patient {patient.patient_id} updated by {current_user.username}")
        
        return PatientResponse(
            id=patient.id,
            patient_id=patient.patient_id,
            first_name=patient.first_name,
            last_name=patient.last_name,
            middle_name=patient.middle_name,
            date_of_birth=patient.date_of_birth,
            gender=patient.gender,
            age=patient.age,
            phone_mobile=patient.phone_mobile,
            email=patient.email,
            full_address=patient.full_address,
            patient_status=patient.patient_status,
            registration_date=patient.registration_date
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update patient error: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update patient"
        )


@router.post("/{patient_id}/vitals", response_model=VitalSignsResponse)
async def create_vital_signs(
    patient_id: int,
    vitals_data: VitalSignsCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Record vital signs for patient"""
    try:
        # Verify patient exists
        stmt = select(Patient).where(Patient.id == patient_id)
        result = await db.execute(stmt)
        patient = result.scalar_one_or_none()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        # Calculate BMI if height and weight provided
        bmi = None
        if vitals_data.height and vitals_data.weight:
            # BMI = weight (lbs) / (height (inches))² × 703
            bmi = (vitals_data.weight / (vitals_data.height ** 2)) * 703
            bmi = round(bmi, 1)
        
        # Create vital signs record
        vital_signs = VitalSigns(
            patient_id=patient_id,
            recorded_by_id=current_user.id,
            recorded_at=datetime.utcnow(),
            systolic_bp=vitals_data.systolic_bp,
            diastolic_bp=vitals_data.diastolic_bp,
            heart_rate=vitals_data.heart_rate,
            respiratory_rate=vitals_data.respiratory_rate,
            temperature=vitals_data.temperature,
            oxygen_saturation=vitals_data.oxygen_saturation,
            height=vitals_data.height,
            weight=vitals_data.weight,
            bmi=bmi,
            pain_scale=vitals_data.pain_scale,
            notes=vitals_data.notes
        )
        
        db.add(vital_signs)
        await db.commit()
        await db.refresh(vital_signs)
        
        logger.info(f"Vital signs recorded for patient {patient.patient_id} by {current_user.username}")
        
        return VitalSignsResponse(
            id=vital_signs.id,
            recorded_at=vital_signs.recorded_at,
            systolic_bp=vital_signs.systolic_bp,
            diastolic_bp=vital_signs.diastolic_bp,
            heart_rate=vital_signs.heart_rate,
            respiratory_rate=vital_signs.respiratory_rate,
            temperature=vital_signs.temperature,
            oxygen_saturation=vital_signs.oxygen_saturation,
            height=vital_signs.height,
            weight=vital_signs.weight,
            bmi=vital_signs.bmi,
            pain_scale=vital_signs.pain_scale,
            notes=vital_signs.notes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create vital signs error: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not record vital signs"
        )


@router.get("/{patient_id}/vitals", response_model=List[VitalSignsResponse])
async def get_patient_vitals(
    patient_id: int,
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get patient's vital signs history"""
    try:
        # Verify patient exists
        stmt = select(Patient).where(Patient.id == patient_id)
        result = await db.execute(stmt)
        patient = result.scalar_one_or_none()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        # Get vital signs
        stmt = select(VitalSigns).where(
            VitalSigns.patient_id == patient_id
        ).order_by(VitalSigns.recorded_at.desc()).limit(limit)
        
        result = await db.execute(stmt)
        vital_signs = result.scalars().all()
        
        return [
            VitalSignsResponse(
                id=vs.id,
                recorded_at=vs.recorded_at,
                systolic_bp=vs.systolic_bp,
                diastolic_bp=vs.diastolic_bp,
                heart_rate=vs.heart_rate,
                respiratory_rate=vs.respiratory_rate,
                temperature=vs.temperature,
                oxygen_saturation=vs.oxygen_saturation,
                height=vs.height,
                weight=vs.weight,
                bmi=vs.bmi,
                pain_scale=vs.pain_scale,
                notes=vs.notes
            )
            for vs in vital_signs
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get patient vitals error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve vital signs"
        )


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete patient (deactivate)"""
    try:
        # Get patient
        stmt = select(Patient).where(Patient.id == patient_id)
        result = await db.execute(stmt)
        patient = result.scalar_one_or_none()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        # Soft delete
        patient.soft_delete()
        patient.updated_by = current_user.username
        
        await db.commit()
        
        logger.info(f"Patient {patient.patient_id} deactivated by {current_user.username}")
        
        return {"message": "Patient deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete patient error: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not delete patient"
        )