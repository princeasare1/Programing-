from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Date, Enum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel
from datetime import datetime, date
import enum


class ClaimStatusEnum(enum.Enum):
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    PENDING = "Pending"
    APPROVED = "Approved"
    DENIED = "Denied"
    PARTIALLY_PAID = "Partially Paid"
    PAID = "Paid"
    REJECTED = "Rejected"
    RESUBMITTED = "Resubmitted"


class PaymentStatusEnum(enum.Enum):
    PENDING = "Pending"
    PAID = "Paid"
    PARTIALLY_PAID = "Partially Paid"
    OVERDUE = "Overdue"
    REFUNDED = "Refunded"
    WRITTEN_OFF = "Written Off"


class ChargeStatusEnum(enum.Enum):
    PENDING = "Pending"
    BILLED = "Billed"
    PAID = "Paid"
    DENIED = "Denied"
    ADJUSTED = "Adjusted"
    VOIDED = "Voided"


class TransactionTypeEnum(enum.Enum):
    CHARGE = "Charge"
    PAYMENT = "Payment"
    ADJUSTMENT = "Adjustment"
    REFUND = "Refund"
    WRITE_OFF = "Write Off"


class InsuranceTypeEnum(enum.Enum):
    PRIMARY = "Primary"
    SECONDARY = "Secondary"
    TERTIARY = "Tertiary"
    SELF_PAY = "Self Pay"


class Encounter(BaseModel):
    """Patient encounters for billing purposes"""
    __tablename__ = "encounters"
    
    # Encounter Information
    encounter_number = Column(String(20), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Encounter Details
    encounter_date = Column(Date, nullable=False)
    encounter_time = Column(DateTime(timezone=True), nullable=False, default=func.now())
    encounter_type = Column(String(50), nullable=False)  # Office Visit, Procedure, etc.
    
    # Location
    location = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    
    # Clinical Information
    diagnosis_codes = Column(JSON, nullable=True, default=list)
    procedure_codes = Column(JSON, nullable=True, default=list)
    
    # Insurance Information
    primary_insurance_id = Column(Integer, ForeignKey("insurance_policies.id"), nullable=True)
    secondary_insurance_id = Column(Integer, ForeignKey("insurance_policies.id"), nullable=True)
    
    # Authorization
    authorization_number = Column(String(50), nullable=True)
    referral_number = Column(String(50), nullable=True)
    
    # Status
    is_billed = Column(Boolean, default=False)
    is_closed = Column(Boolean, default=False)
    
    # Relationships
    patient = relationship("Patient")
    provider = relationship("User")
    primary_insurance = relationship("InsurancePolicy", foreign_keys=[primary_insurance_id])
    secondary_insurance = relationship("InsurancePolicy", foreign_keys=[secondary_insurance_id])
    charges = relationship("Charge", back_populates="encounter")
    claims = relationship("Claim", back_populates="encounter")
    
    def __repr__(self):
        return f"<Encounter {self.encounter_number}: {self.patient_id}>"


class Charge(BaseModel):
    """Individual charges for services rendered"""
    __tablename__ = "charges"
    
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=False)
    
    # Charge Information
    charge_date = Column(Date, nullable=False, default=date.today)
    procedure_code = Column(String(20), nullable=False)  # CPT code
    procedure_description = Column(String(200), nullable=False)
    
    # Modifiers
    modifier_1 = Column(String(2), nullable=True)
    modifier_2 = Column(String(2), nullable=True)
    modifier_3 = Column(String(2), nullable=True)
    modifier_4 = Column(String(2), nullable=True)
    
    # Quantity and Units
    quantity = Column(Integer, nullable=False, default=1)
    units = Column(Integer, nullable=False, default=1)
    
    # Pricing
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    
    # Diagnosis Linking
    diagnosis_pointer = Column(String(20), nullable=True)
    
    # Provider Information
    performing_provider_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    referring_provider_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Status
    status = Column(Enum(ChargeStatusEnum), nullable=False, default=ChargeStatusEnum.PENDING)
    
    # Relationships
    encounter = relationship("Encounter", back_populates="charges")
    performing_provider = relationship("User", foreign_keys=[performing_provider_id])
    referring_provider = relationship("User", foreign_keys=[referring_provider_id])
    claim_lines = relationship("ClaimLine", back_populates="charge")
    
    def __repr__(self):
        return f"<Charge {self.procedure_code}: {self.total_amount}>"


class Claim(BaseModel):
    """Insurance claims for reimbursement"""
    __tablename__ = "claims"
    
    # Claim Information
    claim_number = Column(String(20), unique=True, nullable=False, index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    # Insurance Information
    insurance_policy_id = Column(Integer, ForeignKey("insurance_policies.id"), nullable=False)
    insurance_type = Column(Enum(InsuranceTypeEnum), nullable=False)
    
    # Claim Details
    claim_date = Column(Date, nullable=False, default=date.today)
    service_date_from = Column(Date, nullable=False)
    service_date_to = Column(Date, nullable=True)
    
    # Amounts
    total_charges = Column(Numeric(10, 2), nullable=False)
    allowed_amount = Column(Numeric(10, 2), nullable=True)
    paid_amount = Column(Numeric(10, 2), nullable=True)
    patient_responsibility = Column(Numeric(10, 2), nullable=True)
    
    # Status and Processing
    status = Column(Enum(ClaimStatusEnum), nullable=False, default=ClaimStatusEnum.DRAFT)
    submitted_date = Column(Date, nullable=True)
    processed_date = Column(Date, nullable=True)
    
    # Electronic Submission
    is_electronic = Column(Boolean, default=True)
    clearinghouse_id = Column(String(50), nullable=True)
    transmission_id = Column(String(50), nullable=True)
    
    # Denial Information
    denial_reason = Column(String(500), nullable=True)
    denial_code = Column(String(20), nullable=True)
    
    # Relationships
    encounter = relationship("Encounter", back_populates="claims")
    patient = relationship("Patient")
    insurance_policy = relationship("InsurancePolicy")
    claim_lines = relationship("ClaimLine", back_populates="claim")
    payments = relationship("Payment", back_populates="claim")
    
    def __repr__(self):
        return f"<Claim {self.claim_number}: {self.status}>"


class ClaimLine(BaseModel):
    """Individual line items within a claim"""
    __tablename__ = "claim_lines"
    
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False)
    charge_id = Column(Integer, ForeignKey("charges.id"), nullable=False)
    
    # Line Information
    line_number = Column(Integer, nullable=False)
    
    # Service Details
    service_date = Column(Date, nullable=False)
    procedure_code = Column(String(20), nullable=False)
    diagnosis_code = Column(String(20), nullable=True)
    
    # Amounts
    charged_amount = Column(Numeric(10, 2), nullable=False)
    allowed_amount = Column(Numeric(10, 2), nullable=True)
    paid_amount = Column(Numeric(10, 2), nullable=True)
    adjustment_amount = Column(Numeric(10, 2), nullable=True)
    
    # Status
    line_status = Column(String(20), nullable=False, default="Pending")
    
    # Relationships
    claim = relationship("Claim", back_populates="claim_lines")
    charge = relationship("Charge", back_populates="claim_lines")
    
    def __repr__(self):
        return f"<ClaimLine {self.line_number}: {self.charged_amount}>"


class Payment(BaseModel):
    """Payments received from insurance or patients"""
    __tablename__ = "payments"
    
    # Payment Information
    payment_number = Column(String(20), unique=True, nullable=False, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    # Payment Details
    payment_date = Column(Date, nullable=False)
    payment_amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)  # Check, Credit Card, etc.
    
    # Source
    payer_type = Column(String(50), nullable=False)  # Insurance, Patient, etc.
    payer_name = Column(String(200), nullable=True)
    
    # Check Information
    check_number = Column(String(50), nullable=True)
    check_date = Column(Date, nullable=True)
    
    # Electronic Remittance
    era_number = Column(String(50), nullable=True)
    trace_number = Column(String(50), nullable=True)
    
    # Status
    payment_status = Column(Enum(PaymentStatusEnum), nullable=False, default=PaymentStatusEnum.PENDING)
    
    # Deposit Information
    deposit_date = Column(Date, nullable=True)
    deposit_slip_number = Column(String(50), nullable=True)
    
    # Relationships
    claim = relationship("Claim", back_populates="payments")
    patient = relationship("Patient")
    payment_lines = relationship("PaymentLine", back_populates="payment")
    
    def __repr__(self):
        return f"<Payment {self.payment_number}: {self.payment_amount}>"


class PaymentLine(BaseModel):
    """Individual line items within a payment"""
    __tablename__ = "payment_lines"
    
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
    claim_line_id = Column(Integer, ForeignKey("claim_lines.id"), nullable=True)
    
    # Line Information
    line_number = Column(Integer, nullable=False)
    
    # Service Information
    service_date = Column(Date, nullable=False)
    procedure_code = Column(String(20), nullable=False)
    
    # Amounts
    charged_amount = Column(Numeric(10, 2), nullable=False)
    allowed_amount = Column(Numeric(10, 2), nullable=True)
    paid_amount = Column(Numeric(10, 2), nullable=False)
    adjustment_amount = Column(Numeric(10, 2), nullable=True)
    
    # Reason Codes
    reason_code = Column(String(20), nullable=True)
    reason_description = Column(String(200), nullable=True)
    
    # Relationships
    payment = relationship("Payment", back_populates="payment_lines")
    claim_line = relationship("ClaimLine")
    
    def __repr__(self):
        return f"<PaymentLine {self.line_number}: {self.paid_amount}>"


class Adjustment(BaseModel):
    """Billing adjustments and write-offs"""
    __tablename__ = "adjustments"
    
    # Adjustment Information
    adjustment_number = Column(String(20), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=True)
    
    # Adjustment Details
    adjustment_date = Column(Date, nullable=False, default=date.today)
    adjustment_amount = Column(Numeric(10, 2), nullable=False)
    adjustment_type = Column(String(50), nullable=False)  # Contractual, Write-off, etc.
    
    # Reason
    reason_code = Column(String(20), nullable=True)
    reason_description = Column(String(200), nullable=False)
    
    # User Information
    adjusted_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    patient = relationship("Patient")
    encounter = relationship("Encounter")
    adjusted_by = relationship("User")
    
    def __repr__(self):
        return f"<Adjustment {self.adjustment_number}: {self.adjustment_amount}>"


class PatientStatement(BaseModel):
    """Patient billing statements"""
    __tablename__ = "patient_statements"
    
    # Statement Information
    statement_number = Column(String(20), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    # Statement Details
    statement_date = Column(Date, nullable=False, default=date.today)
    statement_period_from = Column(Date, nullable=False)
    statement_period_to = Column(Date, nullable=False)
    
    # Amounts
    previous_balance = Column(Numeric(10, 2), nullable=False, default=0)
    current_charges = Column(Numeric(10, 2), nullable=False, default=0)
    payments_received = Column(Numeric(10, 2), nullable=False, default=0)
    adjustments = Column(Numeric(10, 2), nullable=False, default=0)
    balance_due = Column(Numeric(10, 2), nullable=False)
    
    # Status
    is_sent = Column(Boolean, default=False)
    sent_date = Column(Date, nullable=True)
    
    # Relationships
    patient = relationship("Patient")
    
    def __repr__(self):
        return f"<PatientStatement {self.statement_number}: {self.balance_due}>"


class PaymentPlan(BaseModel):
    """Patient payment plans"""
    __tablename__ = "payment_plans"
    
    # Plan Information
    plan_number = Column(String(20), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    # Plan Details
    plan_date = Column(Date, nullable=False, default=date.today)
    total_amount = Column(Numeric(10, 2), nullable=False)
    monthly_payment = Column(Numeric(10, 2), nullable=False)
    number_of_payments = Column(Integer, nullable=False)
    
    # Terms
    interest_rate = Column(Numeric(5, 2), nullable=True, default=0)
    down_payment = Column(Numeric(10, 2), nullable=True, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    remaining_balance = Column(Numeric(10, 2), nullable=False)
    
    # Relationships
    patient = relationship("Patient")
    
    def __repr__(self):
        return f"<PaymentPlan {self.plan_number}: {self.remaining_balance}>"


class Transaction(BaseModel):
    """Financial transactions audit trail"""
    __tablename__ = "transactions"
    
    # Transaction Information
    transaction_number = Column(String(20), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    # Transaction Details
    transaction_date = Column(Date, nullable=False, default=date.today)
    transaction_type = Column(Enum(TransactionTypeEnum), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    
    # Description
    description = Column(String(200), nullable=False)
    reference_number = Column(String(50), nullable=True)
    
    # User Information
    processed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    patient = relationship("Patient")
    processed_by = relationship("User")
    
    def __repr__(self):
        return f"<Transaction {self.transaction_number}: {self.amount}>"


class ContractualAdjustment(BaseModel):
    """Contractual adjustments based on payer contracts"""
    __tablename__ = "contractual_adjustments"
    
    # Adjustment Information
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False)
    
    # Adjustment Details
    adjustment_date = Column(Date, nullable=False, default=date.today)
    billed_amount = Column(Numeric(10, 2), nullable=False)
    allowed_amount = Column(Numeric(10, 2), nullable=False)
    adjustment_amount = Column(Numeric(10, 2), nullable=False)
    
    # Contract Information
    contract_rate = Column(Numeric(10, 2), nullable=True)
    contract_type = Column(String(50), nullable=True)
    
    # Relationships
    patient = relationship("Patient")
    claim = relationship("Claim")
    
    def __repr__(self):
        return f"<ContractualAdjustment {self.claim_id}: {self.adjustment_amount}>"


class Copayment(BaseModel):
    """Patient copayments"""
    __tablename__ = "copayments"
    
    # Copayment Information
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=False)
    
    # Copayment Details
    copay_date = Column(Date, nullable=False, default=date.today)
    copay_amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)
    
    # Status
    is_collected = Column(Boolean, default=False)
    collected_date = Column(Date, nullable=True)
    collected_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    patient = relationship("Patient")
    encounter = relationship("Encounter")
    collected_by = relationship("User")
    
    def __repr__(self):
        return f"<Copayment {self.encounter_id}: {self.copay_amount}>"