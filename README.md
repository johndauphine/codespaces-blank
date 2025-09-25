# Customer Data Generator

Generate synthetic (fabricated) customer data for demos, prototypes, local analytics, load/performance tests, or teaching examples.

## Project Structure

```
.
├── pyproject.toml                 # Package metadata & dependencies
├── requirements.txt               # Basic runtime dependency (mirrors pyproject)
├── src/
│   └── customer_data_generator/
│       ├── __init__.py
│       ├── generator.py           # Core record generation logic
│       └── cli.py                 # Argparse-based CLI entry point
├── generate_customers.py          # Backwards-compatible wrapper (deprecated)
├── tests/
│   └── test_generator.py          # Basic unit tests
├── sample-customers.csv           # Example output (optional / may be ignored)
└── README.md
```

## Features

- Deterministic output via `--seed` (including stable customer_id values)
- Adjustable record count (`--count`)
- Locale support (`--locale`, default `en_US`)
- Rich, realistic-ish fields (identity, geo, lifecycle, value, risk)
- Zero-record runs still emit a header-only CSV
- Installable package with console script `customer-gen`
- New: Synthetic patient data generation with `patient-gen` (non-PHI demo data)

## Installation

### Quick (ad‑hoc)
```bash
pip install -r requirements.txt
```

### Editable install (recommended for development)
```bash
pip install -e .[dev]
```

This gives you the `customer-gen` command plus dev tools (`pytest`).

## CLI Usage

Generate 1,000 customers:
```bash
customer-gen --count 1000 --output customers.csv
```

Deterministic dataset (seed):
```bash
customer-gen -c 250 --seed 42 -o customers_seed42.csv
```

Different locale (UK addresses/names):
```bash
customer-gen -c 100 --locale en_GB -o customers_gb.csv
```

Header only (empty dataset):
```bash
customer-gen -c 0 -o empty.csv
```

Backward compatible (legacy) invocation still works:
```bash
python generate_customers.py --count 100 --output legacy.csv
```

### Patient Data
```bash
patient-gen --count 50 --output patients.csv --seed 123
```

Patient fields include (subject to change / expansion):
`patient_id, first_name, last_name, gender, date_of_birth, email, phone, street_address, city, state, postal_code, country, medical_record_number, insurance_provider, insurance_plan, primary_physician, blood_type, height_cm, weight_kg, bmi, smoking_status, chronic_conditions, allergies, medications_current, last_visit_date, next_appointment_date, risk_score, emergency_contact_name, emergency_contact_phone`

Risk score is a synthetic 0–1 metric derived from age, BMI category, chronic condition count, smoking status, plus small noise.

Disclaimer: All patient data is fully fabricated using random generators and should never be treated as real PHI.

## Programmatic Usage
```python
from customer_data_generator import (
    generate_customer_records, generate_customers_csv,
    generate_patient_records, generate_patients_csv
)

for rec in generate_customer_records(3, seed=123):
    print(rec)

generate_customers_csv(50, "sample.csv", seed=99)

patients = list(generate_patient_records(5, seed=42))
generate_patients_csv(25, "patients.csv", seed=42)
```

## Output Schema

| Column | Description |
|--------|-------------|
| customer_id | UUID v4 unique identifier |
| first_name / last_name | Fabricated personal names |
| email | Derived email (not guaranteed globally unique) |
| phone | Locale-specific phone number |
| street_address / city / state / postal_code / country | Geographic info |
| date_of_birth | YYYY-MM-DD (1940–2005) |
| signup_date | ISO-8601 timestamp within last 5 years |
| last_login | ISO-8601 timestamp after signup_date (unless early churn) |
| is_active | Activity flag |
| lifetime_value | Positive skewed float (Gamma distribution) |
| segment | Enterprise / SMB / Consumer / Non-Profit / Education |
| marketing_opt_in | ~60% True |
| referral_source | Acquisition channel |
| credit_score | 300–850 clipped normal |
| churn_risk_score | 0–1 float (lower is better) |

## Testing
```bash
pytest -q
```

## Roadmap Ideas
- Parquet / JSON Lines output options
- Adjustable distributions via config file (YAML / TOML)
- Optional streaming (no in-memory list) for very large datasets
- Performance: multiprocessing / asyncio for large counts

## License
MIT

## Changelog
### 0.2.0 (Unreleased)
- Restructured to `src/` layout, added console script, tests

### 0.1.0
- Initial script-based release
