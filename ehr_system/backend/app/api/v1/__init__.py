from fastapi import APIRouter
from .endpoints import (
    auth, users, patients, appointments, clinical,
    medications, laboratory, billing, analytics
)

api_router = APIRouter()

# Authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# User management routes
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# Patient management routes
api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])

# Appointment scheduling routes
api_router.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])

# Clinical documentation routes
api_router.include_router(clinical.router, prefix="/clinical", tags=["Clinical"])

# Medication management routes
api_router.include_router(medications.router, prefix="/medications", tags=["Medications"])

# Laboratory and radiology routes
api_router.include_router(laboratory.router, prefix="/laboratory", tags=["Laboratory"])

# Billing and claims routes
api_router.include_router(billing.router, prefix="/billing", tags=["Billing"])

# Analytics and reporting routes
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])