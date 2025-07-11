from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Date, Enum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel
from datetime import datetime, date
import enum


class MedicationStatusEnum(enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    DISCONTINUED = "Discontinued"
    RECALLED = "Recalled"


class PrescriptionStatusEnum(enum.Enum):
    PENDING = "Pending"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    EXPIRED = "Expired"
    ON_HOLD = "On Hold"


class FrequencyEnum(enum.Enum):
    ONCE_DAILY = "Once Daily"
    TWICE_DAILY = "Twice Daily"
    THREE_TIMES_DAILY = "Three Times Daily"
    FOUR_TIMES_DAILY = "Four Times Daily"
    EVERY_OTHER_DAY = "Every Other Day"
    WEEKLY = "Weekly"
    AS_NEEDED = "As Needed"
    CUSTOM = "Custom"


class RouteEnum(enum.Enum):
    ORAL = "Oral"
    TOPICAL = "Topical"
    INJECTION = "Injection"
    IV = "Intravenous"
    IM = "Intramuscular"
    SUBLINGUAL = "Sublingual"
    RECTAL = "Rectal"
    INHALATION = "Inhalation"
    OPHTHALMIC = "Ophthalmic"
    OTIC = "Otic"
    NASAL = "Nasal"
    OTHER = "Other"


class UnitEnum(enum.Enum):
    MG = "mg"
    G = "g"
    ML = "ml"
    L = "L"
    TABLET = "tablet"
    CAPSULE = "capsule"
    UNIT = "unit"
    IU = "IU"
    MCG = "mcg"
    DROPS = "drops"
    PUFF = "puff"
    OTHER = "other"


class Medication(BaseModel):
    """Drug formulary and medication information"""
    __tablename__ = "medications"
    
    # Drug Information
    ndc_number = Column(String(12), nullable=True)  # National Drug Code
    drug_name = Column(String(200), nullable=False)
    generic_name = Column(String(200), nullable=False)
    brand_name = Column(String(200), nullable=True)
    
    # Classification
    drug_class = Column(String(100), nullable=True)
    therapeutic_class = Column(String(100), nullable=True)
    controlled_substance_schedule = Column(String(10), nullable=True)
    
    # Dosage Forms
    dosage_form = Column(String(100), nullable=False)  # Tablet, Capsule, Liquid, etc.
    strength = Column(String(50), nullable=False)
    unit = Column(Enum(UnitEnum), nullable=False)
    
    # Identification
    rxcui = Column(String(20), nullable=True)  # RxNorm Concept Unique Identifier
    
    # Formulary Status
    formulary_status = Column(Enum(MedicationStatusEnum), nullable=False, default=MedicationStatusEnum.ACTIVE)
    is_preferred = Column(Boolean, default=False)
    
    # Restrictions
    requires_prior_auth = Column(Boolean, default=False)
    age_restrictions = Column(String(100), nullable=True)
    pregnancy_category = Column(String(10), nullable=True)
    
    # Packaging
    package_size = Column(String(50), nullable=True)
    manufacturer = Column(String(200), nullable=True)
    
    # Cost Information
    awp_unit_price = Column(Numeric(10, 4), nullable=True)  # Average Wholesale Price
    
    # Clinical Information
    indications = Column(Text, nullable=True)
    contraindications = Column(Text, nullable=True)
    warnings = Column(Text, nullable=True)
    side_effects = Column(Text, nullable=True)
    
    # Relationships
    drug_interactions = relationship("DrugInteraction", back_populates="medication")
    prescriptions = relationship("Prescription", back_populates="medication")
    
    def __repr__(self):
        return f"<Medication {self.drug_name}: {self.strength}>"


class DrugInteraction(BaseModel):
    """Drug interaction information"""
    __tablename__ = "drug_interactions"
    
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False)
    interacting_medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False)
    
    # Interaction Details
    interaction_type = Column(String(50), nullable=False)  # Major, Moderate, Minor
    severity = Column(String(20), nullable=False)
    description = Column(Text, nullable=False)
    clinical_effect = Column(Text, nullable=True)
    management = Column(Text, nullable=True)
    
    # Source
    source = Column(String(100), nullable=True)
    last_updated = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Relationships
    medication = relationship("Medication", back_populates="drug_interactions", foreign_keys=[medication_id])
    interacting_medication = relationship("Medication", foreign_keys=[interacting_medication_id])
    
    def __repr__(self):
        return f"<DrugInteraction {self.interaction_type}: {self.severity}>"


class Prescription(BaseModel):
    """Patient prescriptions and medication orders"""
    __tablename__ = "prescriptions"
    
    # Prescription Information
    prescription_number = Column(String(20), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    prescriber_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False)
    
    # Prescription Details
    prescribed_date = Column(Date, nullable=False, default=date.today)
    quantity = Column(Numeric(10, 2), nullable=False)
    quantity_unit = Column(Enum(UnitEnum), nullable=False)
    days_supply = Column(Integer, nullable=False)
    refills_authorized = Column(Integer, nullable=False, default=0)
    refills_remaining = Column(Integer, nullable=False, default=0)
    
    # Dosing Instructions
    dosage_strength = Column(String(50), nullable=False)
    frequency = Column(Enum(FrequencyEnum), nullable=False)
    route = Column(Enum(RouteEnum), nullable=False)
    instructions = Column(Text, nullable=False)
    
    # Status
    status = Column(Enum(PrescriptionStatusEnum), nullable=False, default=PrescriptionStatusEnum.PENDING)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    # Dispensing Information
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"), nullable=True)
    dispensed_date = Column(Date, nullable=True)
    dispensed_quantity = Column(Numeric(10, 2), nullable=True)
    
    # Clinical Information
    indication = Column(String(200), nullable=True)
    diagnosis_codes = Column(JSON, nullable=True, default=list)
    
    # Electronic Prescribing
    is_electronic = Column(Boolean, default=True)
    electronic_signature = Column(String(500), nullable=True)
    transmission_date = Column(DateTime(timezone=True), nullable=True)
    
    # Controlled Substance
    is_controlled_substance = Column(Boolean, default=False)
    dea_schedule = Column(String(10), nullable=True)
    
    # Prior Authorization
    requires_prior_auth = Column(Boolean, default=False)
    prior_auth_number = Column(String(50), nullable=True)
    prior_auth_expiry = Column(Date, nullable=True)
    
    # Generic Substitution
    generic_substitution_allowed = Column(Boolean, default=True)
    
    # Special Instructions
    special_instructions = Column(Text, nullable=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="prescriptions")
    prescriber = relationship("User", back_populates="prescriptions")
    medication = relationship("Medication", back_populates="prescriptions")
    pharmacy = relationship("Pharmacy", back_populates="prescriptions")
    refills = relationship("PrescriptionRefill", back_populates="prescription")
    
    def __repr__(self):
        return f"<Prescription {self.prescription_number}: {self.patient_id}>"


class PrescriptionRefill(BaseModel):
    """Prescription refill tracking"""
    __tablename__ = "prescription_refills"
    
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=False)
    
    # Refill Information
    refill_number = Column(Integer, nullable=False)
    refill_date = Column(Date, nullable=False)
    quantity_dispensed = Column(Numeric(10, 2), nullable=False)
    
    # Pharmacy Information
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"), nullable=True)
    pharmacist_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Payment
    copay_amount = Column(Numeric(10, 2), nullable=True)
    insurance_paid = Column(Numeric(10, 2), nullable=True)
    
    # Status
    refill_status = Column(String(20), nullable=False, default="Completed")
    
    # Relationships
    prescription = relationship("Prescription", back_populates="refills")
    pharmacy = relationship("Pharmacy")
    pharmacist = relationship("User")
    
    def __repr__(self):
        return f"<PrescriptionRefill {self.refill_number}: {self.prescription_id}>"


class Pharmacy(BaseModel):
    """Pharmacy information and inventory"""
    __tablename__ = "pharmacies"
    
    # Pharmacy Information
    pharmacy_name = Column(String(200), nullable=False)
    npi_number = Column(String(20), nullable=True)
    ncpdp_number = Column(String(20), nullable=True)
    
    # Contact Information
    phone = Column(String(20), nullable=True)
    fax = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    
    # Address
    address_line1 = Column(String(100), nullable=True)
    address_line2 = Column(String(100), nullable=True)
    city = Column(String(50), nullable=True)
    state = Column(String(20), nullable=True)
    zip_code = Column(String(10), nullable=True)
    
    # Operating Hours
    hours_of_operation = Column(JSON, nullable=True)
    
    # Services
    services_offered = Column(JSON, nullable=True, default=list)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_preferred = Column(Boolean, default=False)
    
    # Relationships
    prescriptions = relationship("Prescription", back_populates="pharmacy")
    
    def __repr__(self):
        return f"<Pharmacy {self.pharmacy_name}>"


class MedicationHistory(BaseModel):
    """Patient medication history"""
    __tablename__ = "medication_histories"
    
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False)
    
    # History Information
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    
    # Reason for Starting/Stopping
    indication = Column(String(200), nullable=True)
    discontinuation_reason = Column(String(200), nullable=True)
    
    # Source
    source = Column(String(50), nullable=False)  # Prescription, Patient Report, etc.
    recorded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    patient = relationship("Patient")
    medication = relationship("Medication")
    recorded_by = relationship("User")
    
    def __repr__(self):
        return f"<MedicationHistory {self.patient_id}: {self.medication_id}>"


class MedicationAlert(BaseModel):
    """Medication alerts and warnings"""
    __tablename__ = "medication_alerts"
    
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=True)
    
    # Alert Information
    alert_type = Column(String(50), nullable=False)  # Drug Interaction, Allergy, etc.
    severity = Column(String(20), nullable=False)  # High, Medium, Low
    message = Column(Text, nullable=False)
    
    # Alert Source
    source = Column(String(100), nullable=True)
    
    # Status
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    override_reason = Column(String(200), nullable=True)
    
    # Relationships
    patient = relationship("Patient")
    medication = relationship("Medication")
    prescription = relationship("Prescription")
    acknowledged_by = relationship("User")
    
    def __repr__(self):
        return f"<MedicationAlert {self.alert_type}: {self.severity}>"