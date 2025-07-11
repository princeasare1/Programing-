from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Date, Enum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel
from datetime import datetime, date
import enum


class GenderEnum(enum.Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    UNKNOWN = "Unknown"


class MaritalStatusEnum(enum.Enum):
    SINGLE = "Single"
    MARRIED = "Married"
    DIVORCED = "Divorced"
    WIDOWED = "Widowed"
    SEPARATED = "Separated"
    OTHER = "Other"


class BloodTypeEnum(enum.Enum):
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"
    UNKNOWN = "Unknown"


class Patient(BaseModel):
    """Patient model for comprehensive patient management"""
    __tablename__ = "patients"
    
    # Patient Identifiers
    patient_id = Column(String(20), unique=True, nullable=False, index=True)  # MRN
    ssn = Column(String(11), nullable=True)  # Encrypted
    
    # Demographics
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    middle_name = Column(String(50), nullable=True)
    maiden_name = Column(String(50), nullable=True)
    preferred_name = Column(String(50), nullable=True)
    suffix = Column(String(10), nullable=True)  # Jr., Sr., III, etc.
    
    # Basic Information
    date_of_birth = Column(Date, nullable=False)
    gender = Column(Enum(GenderEnum), nullable=False)
    marital_status = Column(Enum(MaritalStatusEnum), nullable=True)
    blood_type = Column(Enum(BloodTypeEnum), nullable=True)
    
    # Contact Information
    phone_home = Column(String(20), nullable=True)
    phone_mobile = Column(String(20), nullable=True)
    phone_work = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    
    # Address
    address_line1 = Column(String(100), nullable=True)
    address_line2 = Column(String(100), nullable=True)
    city = Column(String(50), nullable=True)
    state = Column(String(20), nullable=True)
    zip_code = Column(String(10), nullable=True)
    country = Column(String(50), nullable=True, default="US")
    
    # Demographics
    race = Column(String(50), nullable=True)
    ethnicity = Column(String(50), nullable=True)
    language_primary = Column(String(50), nullable=True, default="English")
    language_secondary = Column(String(50), nullable=True)
    
    # Status
    patient_status = Column(String(20), nullable=False, default="Active")
    registration_date = Column(Date, nullable=False, default=date.today)
    
    # Clinical Information
    primary_care_provider_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    allergies = Column(JSON, nullable=True, default=list)
    medical_conditions = Column(JSON, nullable=True, default=list)
    
    # Emergency Contact
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_relationship = Column(String(50), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_email = Column(String(100), nullable=True)
    
    # Next of Kin
    next_of_kin_name = Column(String(100), nullable=True)
    next_of_kin_relationship = Column(String(50), nullable=True)
    next_of_kin_phone = Column(String(20), nullable=True)
    next_of_kin_email = Column(String(100), nullable=True)
    
    # Special Needs
    special_needs = Column(Text, nullable=True)
    accessibility_requirements = Column(Text, nullable=True)
    
    # Created by
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    created_by_user = relationship("User", back_populates="created_patients", foreign_keys=[created_by_id])
    primary_care_provider = relationship("User", foreign_keys=[primary_care_provider_id])
    insurance_policies = relationship("InsurancePolicy", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient")
    clinical_notes = relationship("ClinicalNote", back_populates="patient")
    prescriptions = relationship("Prescription", back_populates="patient")
    lab_orders = relationship("LabOrder", back_populates="patient")
    lab_results = relationship("LabResult", back_populates="patient")
    vital_signs = relationship("VitalSigns", back_populates="patient")
    
    @property
    def full_name(self):
        """Get patient's full name"""
        name_parts = [self.first_name]
        if self.middle_name:
            name_parts.append(self.middle_name)
        name_parts.append(self.last_name)
        if self.suffix:
            name_parts.append(self.suffix)
        return " ".join(name_parts)
    
    @property
    def age(self):
        """Calculate patient's age"""
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    @property
    def full_address(self):
        """Get formatted address"""
        address_parts = []
        if self.address_line1:
            address_parts.append(self.address_line1)
        if self.address_line2:
            address_parts.append(self.address_line2)
        if self.city:
            address_parts.append(self.city)
        if self.state:
            address_parts.append(self.state)
        if self.zip_code:
            address_parts.append(self.zip_code)
        return ", ".join(address_parts)
    
    def __repr__(self):
        return f"<Patient {self.patient_id}: {self.full_name}>"


class InsurancePolicy(BaseModel):
    """Insurance policy information for patients"""
    __tablename__ = "insurance_policies"
    
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    # Insurance Company
    insurance_company = Column(String(100), nullable=False)
    plan_name = Column(String(100), nullable=True)
    group_number = Column(String(50), nullable=True)
    
    # Policy Information
    policy_number = Column(String(50), nullable=False)
    member_id = Column(String(50), nullable=False)
    subscriber_name = Column(String(100), nullable=True)
    subscriber_relationship = Column(String(50), nullable=True)
    
    # Coverage Details
    coverage_type = Column(String(50), nullable=True)  # Primary, Secondary, etc.
    effective_date = Column(Date, nullable=True)
    expiration_date = Column(Date, nullable=True)
    copay_amount = Column(Numeric(10, 2), nullable=True)
    deductible_amount = Column(Numeric(10, 2), nullable=True)
    
    # Contact Information
    insurance_phone = Column(String(20), nullable=True)
    insurance_address = Column(String(200), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)
    
    # Relationships
    patient = relationship("Patient", back_populates="insurance_policies")
    
    def __repr__(self):
        return f"<InsurancePolicy {self.insurance_company}: {self.policy_number}>"


class PatientNote(BaseModel):
    """General notes about patients"""
    __tablename__ = "patient_notes"
    
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    note_type = Column(String(50), nullable=False)  # General, Alert, etc.
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    is_alert = Column(Boolean, default=False)
    is_confidential = Column(Boolean, default=False)
    
    # Relationships
    patient = relationship("Patient")
    user = relationship("User")
    
    def __repr__(self):
        return f"<PatientNote {self.note_type}: {self.title}>"


class VitalSigns(BaseModel):
    """Patient vital signs tracking"""
    __tablename__ = "vital_signs"
    
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    recorded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Vital Signs
    systolic_bp = Column(Integer, nullable=True)  # mmHg
    diastolic_bp = Column(Integer, nullable=True)  # mmHg
    heart_rate = Column(Integer, nullable=True)  # bpm
    respiratory_rate = Column(Integer, nullable=True)  # breaths/min
    temperature = Column(Numeric(4, 1), nullable=True)  # Fahrenheit
    oxygen_saturation = Column(Integer, nullable=True)  # %
    
    # Measurements
    height = Column(Numeric(5, 2), nullable=True)  # inches
    weight = Column(Numeric(6, 2), nullable=True)  # pounds
    bmi = Column(Numeric(4, 1), nullable=True)
    
    # Additional
    pain_scale = Column(Integer, nullable=True)  # 0-10
    notes = Column(Text, nullable=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="vital_signs")
    recorded_by = relationship("User")
    
    def __repr__(self):
        return f"<VitalSigns {self.patient_id}: {self.recorded_at}>"