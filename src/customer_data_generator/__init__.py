"""Customer Data Generator package."""

from .generator import (
    CustomerRecord,
    generate_customer_records,
    generate_customers_csv,
)
from .patient_generator import (
    PatientRecord,
    generate_patient_records,
    generate_patients_csv,
)

__all__ = [
    "CustomerRecord",
    "generate_customer_records",
    "generate_customers_csv",
    "PatientRecord",
    "generate_patient_records",
    "generate_patients_csv",
]

__version__ = "0.2.0"
