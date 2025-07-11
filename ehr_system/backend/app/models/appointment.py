from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Date, Enum, Numeric, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel
from datetime import datetime, date, time
import enum


class AppointmentStatusEnum(enum.Enum):
    SCHEDULED = "Scheduled"
    CONFIRMED = "Confirmed"
    CHECKED_IN = "Checked In"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    NO_SHOW = "No Show"
    RESCHEDULED = "Rescheduled"


class AppointmentTypeEnum(enum.Enum):
    ROUTINE = "Routine"
    URGENT = "Urgent"
    FOLLOW_UP = "Follow Up"
    CONSULTATION = "Consultation"
    PROCEDURE = "Procedure"
    PHYSICAL_EXAM = "Physical Exam"
    VACCINATION = "Vaccination"
    LAB_WORK = "Lab Work"
    IMAGING = "Imaging"
    THERAPY = "Therapy"
    OTHER = "Other"


class RecurrenceEnum(enum.Enum):
    NONE = "None"
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    YEARLY = "Yearly"


class ReminderTypeEnum(enum.Enum):
    SMS = "SMS"
    EMAIL = "Email"
    PHONE = "Phone"
    PUSH = "Push Notification"


class Appointment(BaseModel):
    """Appointment scheduling and management"""
    __tablename__ = "appointments"
    
    # Core Information
    appointment_id = Column(String(20), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Scheduling Details
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=30)
    end_time = Column(Time, nullable=True)
    
    # Appointment Information
    appointment_type = Column(Enum(AppointmentTypeEnum), nullable=False)
    status = Column(Enum(AppointmentStatusEnum), nullable=False, default=AppointmentStatusEnum.SCHEDULED)
    priority = Column(String(20), nullable=False, default="Normal")  # High, Normal, Low
    
    # Details
    chief_complaint = Column(String(500), nullable=True)
    reason_for_visit = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    
    # Location
    location = Column(String(100), nullable=True)
    room_number = Column(String(20), nullable=True)
    
    # Booking Information
    booked_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    booking_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    booking_source = Column(String(50), nullable=True)  # Online, Phone, Walk-in
    
    # Check-in Information
    checked_in_at = Column(DateTime(timezone=True), nullable=True)
    checked_in_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Completion
    completed_at = Column(DateTime(timezone=True), nullable=True)
    actual_duration = Column(Integer, nullable=True)
    
    # Cancellation
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    cancellation_reason = Column(String(500), nullable=True)
    
    # Rescheduling
    rescheduled_from_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    rescheduled_to_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    
    # Insurance
    insurance_verified = Column(Boolean, default=False)
    copay_amount = Column(Numeric(10, 2), nullable=True)
    copay_collected = Column(Boolean, default=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    provider = relationship("User", back_populates="appointments")
    booked_by = relationship("User", foreign_keys=[booked_by_id])
    checked_in_by = relationship("User", foreign_keys=[checked_in_by_id])
    cancelled_by = relationship("User", foreign_keys=[cancelled_by_id])
    rescheduled_from = relationship("Appointment", remote_side=[id], foreign_keys=[rescheduled_from_id])
    rescheduled_to = relationship("Appointment", remote_side=[id], foreign_keys=[rescheduled_to_id])
    reminders = relationship("AppointmentReminder", back_populates="appointment")
    
    @property
    def datetime(self):
        """Get appointment datetime"""
        return datetime.combine(self.appointment_date, self.appointment_time)
    
    def can_be_cancelled(self):
        """Check if appointment can be cancelled"""
        return self.status in [AppointmentStatusEnum.SCHEDULED, AppointmentStatusEnum.CONFIRMED]
    
    def can_be_rescheduled(self):
        """Check if appointment can be rescheduled"""
        return self.status in [AppointmentStatusEnum.SCHEDULED, AppointmentStatusEnum.CONFIRMED]
    
    def __repr__(self):
        return f"<Appointment {self.appointment_id}: {self.patient_id}>"


class AppointmentReminder(BaseModel):
    """Appointment reminder notifications"""
    __tablename__ = "appointment_reminders"
    
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    
    # Reminder Configuration
    reminder_type = Column(Enum(ReminderTypeEnum), nullable=False)
    reminder_time = Column(Integer, nullable=False)  # Minutes before appointment
    
    # Delivery
    scheduled_for = Column(DateTime(timezone=True), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    is_sent = Column(Boolean, default=False)
    
    # Content
    subject = Column(String(200), nullable=True)
    message = Column(Text, nullable=True)
    
    # Delivery Status
    delivery_status = Column(String(50), nullable=True)
    error_message = Column(String(500), nullable=True)
    
    # Relationships
    appointment = relationship("Appointment", back_populates="reminders")
    
    def __repr__(self):
        return f"<AppointmentReminder {self.reminder_type}: {self.appointment_id}>"


class ProviderSchedule(BaseModel):
    """Provider availability and schedule"""
    __tablename__ = "provider_schedules"
    
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Schedule Details
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    
    # Availability
    is_available = Column(Boolean, default=True)
    max_appointments = Column(Integer, nullable=True)
    
    # Break Times
    break_start = Column(Time, nullable=True)
    break_end = Column(Time, nullable=True)
    
    # Effective Dates
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    
    # Relationships
    provider = relationship("User")
    
    def __repr__(self):
        return f"<ProviderSchedule {self.provider_id}: {self.day_of_week}>"


class ScheduleException(BaseModel):
    """Schedule exceptions for holidays, time off, etc."""
    __tablename__ = "schedule_exceptions"
    
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Exception Details
    exception_date = Column(Date, nullable=False)
    exception_type = Column(String(50), nullable=False)  # Holiday, Vacation, Sick, etc.
    
    # Time Range
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    is_all_day = Column(Boolean, default=True)
    
    # Details
    reason = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    provider = relationship("User")
    
    def __repr__(self):
        return f"<ScheduleException {self.provider_id}: {self.exception_date}>"


class AppointmentType(BaseModel):
    """Configuration for different appointment types"""
    __tablename__ = "appointment_types"
    
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=30)
    color = Column(String(7), nullable=True)  # Hex color code
    
    # Booking Rules
    advance_booking_days = Column(Integer, nullable=True)
    same_day_booking = Column(Boolean, default=True)
    requires_referral = Column(Boolean, default=False)
    
    # Requirements
    requires_insurance_verification = Column(Boolean, default=False)
    requires_copay = Column(Boolean, default=False)
    
    # Instructions
    patient_instructions = Column(Text, nullable=True)
    provider_instructions = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<AppointmentType {self.name}>"


class WaitingList(BaseModel):
    """Patient waiting list for earlier appointments"""
    __tablename__ = "waiting_lists"
    
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Waiting List Details
    appointment_type = Column(Enum(AppointmentTypeEnum), nullable=False)
    preferred_date = Column(Date, nullable=True)
    preferred_time = Column(Time, nullable=True)
    
    # Flexibility
    date_flexibility_days = Column(Integer, nullable=True, default=7)
    time_flexibility_minutes = Column(Integer, nullable=True, default=60)
    
    # Contact Information
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(100), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    notified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    patient = relationship("Patient")
    provider = relationship("User")
    
    def __repr__(self):
        return f"<WaitingList {self.patient_id}: {self.appointment_type}>"


class RecurringAppointment(BaseModel):
    """Recurring appointment patterns"""
    __tablename__ = "recurring_appointments"
    
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Recurrence Pattern
    recurrence_type = Column(Enum(RecurrenceEnum), nullable=False)
    recurrence_interval = Column(Integer, nullable=False, default=1)
    
    # Appointment Details
    appointment_type = Column(Enum(AppointmentTypeEnum), nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=30)
    
    # Schedule
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    time_slot = Column(Time, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    patient = relationship("Patient")
    provider = relationship("User")
    
    def __repr__(self):
        return f"<RecurringAppointment {self.patient_id}: {self.recurrence_type}>"