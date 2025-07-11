from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Date, Enum, Numeric, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel
from datetime import datetime, date
import enum


class OrderStatusEnum(enum.Enum):
    PENDING = "Pending"
    ORDERED = "Ordered"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    RESULTED = "Resulted"


class SpecimenTypeEnum(enum.Enum):
    BLOOD = "Blood"
    URINE = "Urine"
    STOOL = "Stool"
    SALIVA = "Saliva"
    TISSUE = "Tissue"
    SWAB = "Swab"
    FLUID = "Fluid"
    OTHER = "Other"


class PriorityEnum(enum.Enum):
    STAT = "STAT"
    URGENT = "Urgent"
    ROUTINE = "Routine"
    TIMED = "Timed"


class ResultStatusEnum(enum.Enum):
    PENDING = "Pending"
    PRELIMINARY = "Preliminary"
    FINAL = "Final"
    CORRECTED = "Corrected"
    CANCELLED = "Cancelled"
    AMENDED = "Amended"


class AbnormalFlagEnum(enum.Enum):
    NORMAL = "Normal"
    HIGH = "High"
    LOW = "Low"
    ABNORMAL = "Abnormal"
    CRITICAL = "Critical"


class LabOrder(BaseModel):
    """Laboratory test orders"""
    __tablename__ = "lab_orders"
    
    # Order Information
    order_number = Column(String(20), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    ordering_provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Order Details
    order_date = Column(Date, nullable=False, default=date.today)
    order_time = Column(DateTime(timezone=True), nullable=False, default=func.now())
    priority = Column(Enum(PriorityEnum), nullable=False, default=PriorityEnum.ROUTINE)
    status = Column(Enum(OrderStatusEnum), nullable=False, default=OrderStatusEnum.PENDING)
    
    # Clinical Information
    diagnosis_codes = Column(JSON, nullable=True, default=list)
    clinical_indication = Column(String(500), nullable=True)
    fasting_required = Column(Boolean, default=False)
    
    # Collection Information
    collection_date = Column(Date, nullable=True)
    collection_time = Column(DateTime(timezone=True), nullable=True)
    collected_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Specimen Information
    specimen_type = Column(Enum(SpecimenTypeEnum), nullable=True)
    collection_method = Column(String(100), nullable=True)
    collection_site = Column(String(100), nullable=True)
    
    # Laboratory Information
    lab_id = Column(Integer, ForeignKey("laboratories.id"), nullable=True)
    external_order_id = Column(String(50), nullable=True)
    
    # Special Instructions
    special_instructions = Column(Text, nullable=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="lab_orders")
    ordering_provider = relationship("User", back_populates="lab_orders")
    collected_by = relationship("User", foreign_keys=[collected_by_id])
    laboratory = relationship("Laboratory", back_populates="orders")
    tests = relationship("LabTest", back_populates="order")
    results = relationship("LabResult", back_populates="order")
    
    def __repr__(self):
        return f"<LabOrder {self.order_number}: {self.patient_id}>"


class LabTest(BaseModel):
    """Individual laboratory tests within an order"""
    __tablename__ = "lab_tests"
    
    order_id = Column(Integer, ForeignKey("lab_orders.id"), nullable=False)
    
    # Test Information
    test_code = Column(String(20), nullable=False)  # CPT or LOINC code
    test_name = Column(String(200), nullable=False)
    test_category = Column(String(100), nullable=True)
    
    # Test Details
    methodology = Column(String(100), nullable=True)
    specimen_required = Column(String(100), nullable=True)
    
    # Status
    test_status = Column(Enum(OrderStatusEnum), nullable=False, default=OrderStatusEnum.PENDING)
    
    # Relationships
    order = relationship("LabOrder", back_populates="tests")
    results = relationship("LabResult", back_populates="test")
    
    def __repr__(self):
        return f"<LabTest {self.test_code}: {self.test_name}>"


class LabResult(BaseModel):
    """Laboratory test results"""
    __tablename__ = "lab_results"
    
    order_id = Column(Integer, ForeignKey("lab_orders.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("lab_tests.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    # Result Information
    result_value = Column(String(100), nullable=True)
    result_unit = Column(String(50), nullable=True)
    reference_range = Column(String(100), nullable=True)
    
    # Status
    result_status = Column(Enum(ResultStatusEnum), nullable=False, default=ResultStatusEnum.PENDING)
    abnormal_flag = Column(Enum(AbnormalFlagEnum), nullable=True)
    
    # Timing
    result_date = Column(Date, nullable=True)
    result_time = Column(DateTime(timezone=True), nullable=True)
    reviewed_date = Column(DateTime(timezone=True), nullable=True)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Comments
    result_comment = Column(Text, nullable=True)
    lab_comment = Column(Text, nullable=True)
    
    # Quality Control
    is_critical = Column(Boolean, default=False)
    critical_notified = Column(Boolean, default=False)
    critical_notification_time = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    order = relationship("LabOrder", back_populates="results")
    test = relationship("LabTest", back_populates="results")
    patient = relationship("Patient", back_populates="lab_results")
    reviewed_by = relationship("User")
    
    def __repr__(self):
        return f"<LabResult {self.test_id}: {self.result_value}>"


class Laboratory(BaseModel):
    """Laboratory facility information"""
    __tablename__ = "laboratories"
    
    # Lab Information
    lab_name = Column(String(200), nullable=False)
    lab_code = Column(String(20), unique=True, nullable=False)
    clia_number = Column(String(15), nullable=True)  # Clinical Laboratory Improvement Amendments
    
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
    
    # Service Information
    services_offered = Column(JSON, nullable=True, default=list)
    specialties = Column(JSON, nullable=True, default=list)
    
    # Integration
    lis_interface = Column(String(100), nullable=True)  # Laboratory Information System
    result_delivery_method = Column(String(50), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_preferred = Column(Boolean, default=False)
    
    # Relationships
    orders = relationship("LabOrder", back_populates="laboratory")
    
    def __repr__(self):
        return f"<Laboratory {self.lab_name}>"


class RadiologyOrder(BaseModel):
    """Radiology and imaging orders"""
    __tablename__ = "radiology_orders"
    
    # Order Information
    order_number = Column(String(20), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    ordering_provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Order Details
    order_date = Column(Date, nullable=False, default=date.today)
    order_time = Column(DateTime(timezone=True), nullable=False, default=func.now())
    priority = Column(Enum(PriorityEnum), nullable=False, default=PriorityEnum.ROUTINE)
    status = Column(Enum(OrderStatusEnum), nullable=False, default=OrderStatusEnum.PENDING)
    
    # Imaging Information
    modality = Column(String(50), nullable=False)  # CT, MRI, X-Ray, etc.
    body_part = Column(String(100), nullable=False)
    procedure_code = Column(String(20), nullable=True)  # CPT code
    procedure_name = Column(String(200), nullable=False)
    
    # Clinical Information
    diagnosis_codes = Column(JSON, nullable=True, default=list)
    clinical_indication = Column(String(500), nullable=True)
    clinical_history = Column(Text, nullable=True)
    
    # Contrast Information
    contrast_required = Column(Boolean, default=False)
    contrast_type = Column(String(50), nullable=True)
    contrast_allergies = Column(String(200), nullable=True)
    
    # Scheduling
    scheduled_date = Column(Date, nullable=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=True)
    
    # Facility Information
    imaging_facility_id = Column(Integer, ForeignKey("imaging_facilities.id"), nullable=True)
    
    # Special Instructions
    special_instructions = Column(Text, nullable=True)
    patient_preparation = Column(Text, nullable=True)
    
    # Relationships
    patient = relationship("Patient")
    ordering_provider = relationship("User")
    imaging_facility = relationship("ImagingFacility", back_populates="orders")
    studies = relationship("RadiologyStudy", back_populates="order")
    
    def __repr__(self):
        return f"<RadiologyOrder {self.order_number}: {self.procedure_name}>"


class RadiologyStudy(BaseModel):
    """Radiology study and imaging results"""
    __tablename__ = "radiology_studies"
    
    order_id = Column(Integer, ForeignKey("radiology_orders.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    # Study Information
    study_instance_uid = Column(String(100), unique=True, nullable=False)  # DICOM UID
    accession_number = Column(String(50), nullable=True)
    study_date = Column(Date, nullable=False)
    study_time = Column(DateTime(timezone=True), nullable=False)
    
    # Technical Information
    modality = Column(String(50), nullable=False)
    study_description = Column(String(200), nullable=False)
    number_of_series = Column(Integer, nullable=True)
    number_of_images = Column(Integer, nullable=True)
    
    # Personnel
    technologist = Column(String(100), nullable=True)
    radiologist_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Status
    study_status = Column(Enum(ResultStatusEnum), nullable=False, default=ResultStatusEnum.PENDING)
    
    # Report Information
    report_date = Column(Date, nullable=True)
    report_time = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    order = relationship("RadiologyOrder", back_populates="studies")
    patient = relationship("Patient")
    radiologist = relationship("User")
    reports = relationship("RadiologyReport", back_populates="study")
    images = relationship("RadiologyImage", back_populates="study")
    
    def __repr__(self):
        return f"<RadiologyStudy {self.study_instance_uid}>"


class RadiologyReport(BaseModel):
    """Radiology interpretation reports"""
    __tablename__ = "radiology_reports"
    
    study_id = Column(Integer, ForeignKey("radiology_studies.id"), nullable=False)
    radiologist_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Report Content
    clinical_history = Column(Text, nullable=True)
    technique = Column(Text, nullable=True)
    findings = Column(Text, nullable=False)
    impression = Column(Text, nullable=False)
    recommendations = Column(Text, nullable=True)
    
    # Report Status
    report_status = Column(Enum(ResultStatusEnum), nullable=False, default=ResultStatusEnum.PRELIMINARY)
    
    # Timing
    dictated_date = Column(DateTime(timezone=True), nullable=True)
    transcribed_date = Column(DateTime(timezone=True), nullable=True)
    signed_date = Column(DateTime(timezone=True), nullable=True)
    
    # Quality Assurance
    is_critical = Column(Boolean, default=False)
    critical_notification_sent = Column(Boolean, default=False)
    
    # Relationships
    study = relationship("RadiologyStudy", back_populates="reports")
    radiologist = relationship("User")
    
    def __repr__(self):
        return f"<RadiologyReport {self.study_id}: {self.radiologist_id}>"


class RadiologyImage(BaseModel):
    """Radiology image storage and metadata"""
    __tablename__ = "radiology_images"
    
    study_id = Column(Integer, ForeignKey("radiology_studies.id"), nullable=False)
    
    # Image Information
    sop_instance_uid = Column(String(100), unique=True, nullable=False)  # DICOM SOP Instance UID
    series_instance_uid = Column(String(100), nullable=False)  # DICOM Series Instance UID
    image_number = Column(Integer, nullable=True)
    
    # Image Details
    image_type = Column(String(50), nullable=True)
    image_position = Column(String(100), nullable=True)
    image_orientation = Column(String(100), nullable=True)
    
    # File Information
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_format = Column(String(20), nullable=True)  # DICOM, JPEG, etc.
    
    # Thumbnail
    thumbnail_path = Column(String(500), nullable=True)
    
    # Relationships
    study = relationship("RadiologyStudy", back_populates="images")
    
    def __repr__(self):
        return f"<RadiologyImage {self.sop_instance_uid}>"


class ImagingFacility(BaseModel):
    """Imaging facility information"""
    __tablename__ = "imaging_facilities"
    
    # Facility Information
    facility_name = Column(String(200), nullable=False)
    facility_code = Column(String(20), unique=True, nullable=False)
    
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
    
    # Equipment and Services
    modalities_available = Column(JSON, nullable=True, default=list)
    services_offered = Column(JSON, nullable=True, default=list)
    
    # Hours of Operation
    hours_of_operation = Column(JSON, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_preferred = Column(Boolean, default=False)
    
    # Relationships
    orders = relationship("RadiologyOrder", back_populates="imaging_facility")
    
    def __repr__(self):
        return f"<ImagingFacility {self.facility_name}>"


class CriticalResult(BaseModel):
    """Critical results requiring immediate notification"""
    __tablename__ = "critical_results"
    
    # Result Information
    result_type = Column(String(50), nullable=False)  # Lab, Radiology
    result_id = Column(Integer, nullable=False)  # ID of lab_results or radiology_reports
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    # Critical Details
    critical_value = Column(String(200), nullable=False)
    critical_reason = Column(String(500), nullable=False)
    
    # Notification
    notification_sent = Column(Boolean, default=False)
    notification_method = Column(String(50), nullable=True)
    notification_time = Column(DateTime(timezone=True), nullable=True)
    notified_provider_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Acknowledgment
    acknowledged = Column(Boolean, default=False)
    acknowledged_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    patient = relationship("Patient")
    notified_provider = relationship("User", foreign_keys=[notified_provider_id])
    acknowledged_by = relationship("User", foreign_keys=[acknowledged_by_id])
    
    def __repr__(self):
        return f"<CriticalResult {self.result_type}: {self.patient_id}>"