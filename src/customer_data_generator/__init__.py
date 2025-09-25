"""Customer Data Generator package."""

from .generator import (
    CustomerRecord,
    generate_customer_records,
    generate_customers_csv,
)

__all__ = [
    "CustomerRecord",
    "generate_customer_records",
    "generate_customers_csv",
]

__version__ = "0.2.0"
