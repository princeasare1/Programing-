from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Date, Enum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel
from datetime import datetime, date
import enum


class NoteTypeEnum(enum.Enum):
    SOAP = "SOAP"
    PROGRESS = "Progress Note"
    DISCHARGE = "Discharge Summary"
    CONSULTATION = "Consultation"
    ADMISSION = "Admission Note"
    OPERATIVE = "Operative Note"
    PROCEDURE = "Procedure Note"
    NURSING = "Nursing Note"
    OTHER = "Other"


class DiagnosisTypeEnum(enum.Enum):
    PRIMARY = "Primary"
    SECONDARY = "Secondary"
    DIFFERENTIAL = "Differential"
    RULE_OUT = "Rule Out"
    CHRONIC = "Chronic"
    ACUTE = "Acute"


class SeverityEnum(enum.Enum):
    MILD = "Mild"
    MODERATE = "Moderate"
    SEVERE = "Severe"
    CRITICAL = "Critical"


class StatusEnum(enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    RESOLVED = "Resolved"
    CHRONIC = "Chronic"
    RECURRENT = "Recurrent"


class ClinicalNote(BaseModel):
    """Clinical documentation including SOAP notes"""
    __tablename__ = "clinical_notes"
    
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Note Details
    note_type = Column(Enum(NoteTypeEnum), nullable=False)
    title = Column(String(200), nullable=True)
    encounter_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # SOAP Components
    subjective = Column(Text, nullable=True)  # Patient's description of symptoms
    objective = Column(Text, nullable=True)  # Physical findings, vital signs
    assessment = Column(Text, nullable=True)  # Clinical impression, diagnoses
    plan = Column(Text, nullable=True)  # Treatment plan, medications, follow-up
    
    # Additional Components
    chief_complaint = Column(String(500), nullable=True)
    history_present_illness = Column(Text, nullable=True)
    past_medical_history = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)
    social_history = Column(Text, nullable=True)
    family_history = Column(Text, nullable=True)
    review_of_systems = Column(Text, nullable=True)
    physical_examination = Column(Text, nullable=True)
    
    # Structured Data
    vital_signs_id = Column(Integer, ForeignKey("vital_signs.id"), nullable=True)
    
    # Templates and Coding
    template_used = Column(String(100), nullable=True)
    icd_codes = Column(JSON, nullable=True, default=list)
    cpt_codes = Column(JSON, nullable=True, default=list)
    
    # Status
    is_finalized = Column(Boolean, default=False)
    finalized_at = Column(DateTime(timezone=True), nullable=True)
    is_amended = Column(Boolean, default=False)
    amendment_reason = Column(Text, nullable=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="clinical_notes")
    provider = relationship("User", back_populates="clinical_notes")
    vital_signs = relationship("VitalSigns")
    diagnoses = relationship("Diagnosis", back_populates="clinical_note")
    
    def __repr__(self):
        return f"<ClinicalNote {self.note_type}: {self.patient_id}>"


class Diagnosis(BaseModel):
    """Patient diagnoses with ICD coding"""
    __tablename__ = "diagnoses"
    
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    clinical_note_id = Column(Integer, ForeignKey("clinical_notes.id"), nullable=True)
    
    # Diagnosis Information
    diagnosis_code = Column(String(20), nullable=False)  # ICD-10 code
    diagnosis_description = Column(String(500), nullable=False)
    diagnosis_type = Column(Enum(DiagnosisTypeEnum), nullable=False)
    
    # Clinical Details
    severity = Column(Enum(SeverityEnum), nullable=True)
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.ACTIVE)
    onset_date = Column(Date, nullable=True)
    resolution_date = Column(Date, nullable=True)
    
    # Additional Information
    laterality = Column(String(20), nullable=True)  # Left, Right, Bilateral
    stage = Column(String(50), nullable=True)
    grade = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Coding
    icd_version = Column(String(10), nullable=False, default="ICD-10")
    snomed_code = Column(String(20), nullable=True)
    
    # Relationships
    patient = relationship("Patient")
    provider = relationship("User")
    clinical_note = relationship("ClinicalNote", back_populates="diagnoses")
    
    def __repr__(self):
        return f"<Diagnosis {self.diagnosis_code}: {self.diagnosis_description}>"


class Allergy(BaseModel):
    """Patient allergies and adverse reactions"""
    __tablename__ = "allergies"
    
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Allergy Information
    allergen = Column(String(200), nullable=False)
    allergen_type = Column(String(50), nullable=False)  # Drug, Food, Environmental
    reaction = Column(String(500), nullable=False)
    severity = Column(Enum(SeverityEnum), nullable=False)
    
    # Details
    onset_date = Column(Date, nullable=True)
    reaction_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Status
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.ACTIVE)
    verified = Column(Boolean, default=False)
    
    # Relationships
    patient = relationship("Patient")
    provider = relationship("User")
    
    def __repr__(self):
        return f"<Allergy {self.allergen}: {self.severity}>"


class ProblemList(BaseModel):
    """Patient problem list for ongoing issues"""
    __tablename__ = "problem_lists"
    
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Problem Information
    problem_description = Column(String(500), nullable=False)
    problem_code = Column(String(20), nullable=True)  # ICD-10 code
    priority = Column(String(20), nullable=False, default="Medium")  # High, Medium, Low
    
    # Status
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.ACTIVE)
    onset_date = Column(Date, nullable=True)
    resolved_date = Column(Date, nullable=True)
    
    # Clinical Details
    severity = Column(Enum(SeverityEnum), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    patient = relationship("Patient")
    provider = relationship("User")
    
    def __repr__(self):
        return f"<ProblemList {self.problem_description}>"


class ClinicalTemplate(BaseModel):
    """Templates for clinical documentation"""
    __tablename__ = "clinical_templates"
    
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    specialty = Column(String(100), nullable=True)
    note_type = Column(Enum(NoteTypeEnum), nullable=False)
    
    # Template Content
    template_content = Column(JSON, nullable=False)
    
    # Usage
    is_active = Column(Boolean, default=True)
    is_system_template = Column(Boolean, default=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    created_by = relationship("User")
    
    def __repr__(self):
        return f"<ClinicalTemplate {self.name}>"


class Assessment(BaseModel):
    """Clinical assessments and evaluations"""
    __tablename__ = "assessments"
    
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    clinical_note_id = Column(Integer, ForeignKey("clinical_notes.id"), nullable=True)
    
    # Assessment Information
    assessment_type = Column(String(100), nullable=False)  # Pain, Functional, etc.
    assessment_tool = Column(String(100), nullable=True)  # Scale or tool used
    score = Column(Numeric(10, 2), nullable=True)
    max_score = Column(Numeric(10, 2), nullable=True)
    
    # Results
    result_summary = Column(Text, nullable=False)
    interpretation = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    
    # Assessment Date
    assessment_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Relationships
    patient = relationship("Patient")
    provider = relationship("User")
    clinical_note = relationship("ClinicalNote")
    
    def __repr__(self):
        return f"<Assessment {self.assessment_type}: {self.patient_id}>"


class ClinicalObservation(BaseModel):
    """Clinical observations and findings"""
    __tablename__ = "clinical_observations"
    
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    clinical_note_id = Column(Integer, ForeignKey("clinical_notes.id"), nullable=True)
    
    # Observation Details
    observation_type = Column(String(100), nullable=False)
    observation_code = Column(String(20), nullable=True)  # LOINC or SNOMED
    observation_value = Column(String(100), nullable=True)
    unit_of_measure = Column(String(50), nullable=True)
    
    # Reference Ranges
    reference_range_low = Column(Numeric(10, 2), nullable=True)
    reference_range_high = Column(Numeric(10, 2), nullable=True)
    is_abnormal = Column(Boolean, default=False)
    
    # Timing
    observation_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Additional Information
    method = Column(String(100), nullable=True)
    site = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    patient = relationship("Patient")
    provider = relationship("User")
    clinical_note = relationship("ClinicalNote")
    
    def __repr__(self):
        return f"<ClinicalObservation {self.observation_type}: {self.observation_value}>"