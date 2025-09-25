# Customer Data Generator

Python utility to generate fabricated (synthetic) customer data for demos, testing, analytics prototypes, or load testing.

## Features

- Deterministic output with `--seed`
- Adjustable number of records via `--count`
- Locale support (defaults to `en_US`)
- Rich fields: identity, contact, geography, lifecycle, value metrics, risk metrics
- Writes a single CSV with header

## Install

Create / activate a virtual environment (optional) then install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Generate 1000 customers:

```bash
python generate_customers.py --count 1000 --output customers.csv
```

Deterministic (repeatable) dataset:

```bash
python generate_customers.py --count 250 --seed 42 --output customers_seed42.csv
```

Different locale (e.g., Great Britain):

```bash
python generate_customers.py --count 100 --locale en_GB --output customers_gb.csv
```

Empty file with header only (count 0):

```bash
python generate_customers.py --count 0 --output empty.csv
```

## Programmatic Use

```python
from generate_customers import generate_customer_records, generate_customers_csv

for record in generate_customer_records(5, seed=123):
    print(record)

generate_customers_csv(100, "sample.csv", seed=999)
```

## Output Schema

| Column | Description |
|--------|-------------|
| customer_id | UUID v4 unique identifier |
| first_name / last_name | Fabricated personal names |
| email | Derived email (may not be globally unique) |
| phone | Phone number (format varies by locale) |
| street_address / city / state / postal_code / country | Geographical info |
| date_of_birth | YYYY-MM-DD birth date (1940-2005 range) |
| signup_date | ISO timestamp within last 5 years |
| last_login | ISO timestamp after signup_date (unless quickly churned) |
| is_active | Boolean indicating recent activity likelihood |
| lifetime_value | Skewed positive float (USD-like) |
| segment | Market segment category |
| marketing_opt_in | True if user opted into marketing (~60%) |
| referral_source | How the customer was acquired |
| credit_score | Simulated credit score (300-850) |
| churn_risk_score | Float 0-1 (lower is better) |

## License

MIT
