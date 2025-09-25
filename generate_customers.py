#!/usr/bin/env python3
"""Generate fabricated customer data and write to a single CSV file.

Usage (CLI):
    python generate_customers.py --count 1000 --output customers.csv

Programmatic:
    from generate_customers import generate_customers_csv
    generate_customers_csv(count=500, path="customers.csv")

Fields:
    customer_id: UUID4
    first_name, last_name, email, phone
    street_address, city, state, postal_code, country
    date_of_birth (YYYY-MM-DD) between 1940-01-01 and 2005-12-31
    signup_date (ISO 8601) within last 5 years
    last_login (ISO 8601) after signup_date
    is_active (bool)
    lifetime_value (floating USD ~ gamma distribution)
    segment (enum: Enterprise, SMB, Consumer, Non-Profit, Education)
    marketing_opt_in (bool)
    referral_source (enum)
    credit_score (300-850)
    churn_risk_score (0-1 float with 3 decimals)
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
import uuid
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Optional

from faker import Faker


SEGMENTS = ["Enterprise", "SMB", "Consumer", "Non-Profit", "Education"]
REFERRAL_SOURCES = [
    "Organic Search",
    "Paid Search",
    "Social Media",
    "Referral",
    "Email Campaign",
    "Event",
    "Direct",
    "Affiliate",
]


@dataclass
class CustomerRecord:
    customer_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    street_address: str
    city: str
    state: str
    postal_code: str
    country: str
    date_of_birth: str
    signup_date: str
    last_login: str
    is_active: bool
    lifetime_value: float
    segment: str
    marketing_opt_in: bool
    referral_source: str
    credit_score: int
    churn_risk_score: float


def _random_date(faker: Faker, start: date, end: date) -> date:
    """Return a random date between start and end inclusive."""
    delta_days = (end - start).days
    return start + timedelta(days=faker.random_int(min=0, max=delta_days))


def _generate_one(faker: Faker) -> CustomerRecord:
    # Birth date between 1940 and 2005
    dob = _random_date(
        faker,
        date(1940, 1, 1),
        date(2005, 12, 31),
    )

    # Signup within last 5 years
    now = datetime.utcnow()
    signup_start = now - timedelta(days=5 * 365)
    signup_dt = faker.date_time_between(start_date=signup_start, end_date=now)
    # Last login after signup (80% active)
    if faker.random.random() < 0.8:
        last_login_dt = faker.date_time_between(start_date=signup_dt, end_date=now)
        is_active = True
    else:
        # Inactive: last login near signup date
        last_login_dt = signup_dt + timedelta(hours=faker.random_int(min=0, max=72))
        is_active = False

    # Lifetime value using gamma shape to skew higher values rarer
    lifetime_value = round(random.gammavariate(2.5, 120), 2)  # shape k, scale theta

    segment = random.choices(
        SEGMENTS,
        weights=[0.15, 0.25, 0.45, 0.05, 0.10],
        k=1,
    )[0]
    referral_source = random.choice(REFERRAL_SOURCES)

    # Credit score normal-ish distribution clipped 300-850
    credit_score = int(min(850, max(300, random.gauss(690, 60))))

    # Churn risk as inverse function of activity, segment, and lifetime value pattern
    base_risk = 0.5
    if is_active:
        base_risk -= 0.15
    if segment == "Enterprise":
        base_risk -= 0.10
    elif segment == "Consumer":
        base_risk += 0.05
    # More value => less churn risk
    base_risk -= min(0.20, lifetime_value / 10000)
    # Add noise
    base_risk += random.uniform(-0.05, 0.05)
    churn_risk = round(min(1.0, max(0.0, base_risk)), 3)

    first_name = faker.first_name()
    last_name = faker.last_name()
    domain = faker.free_email_domain()
    email = f"{first_name.lower()}.{last_name.lower()}@{domain}".replace("'", "")

    return CustomerRecord(
        customer_id=str(uuid.uuid4()),
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=faker.phone_number(),
        street_address=faker.street_address().replace("\n", ", "),
        city=faker.city(),
        state=faker.state_abbr() if hasattr(faker, "state_abbr") else faker.state(),
        postal_code=faker.postcode(),
        country=faker.current_country() if hasattr(faker, "current_country") else faker.country(),
        date_of_birth=dob.isoformat(),
        signup_date=signup_dt.isoformat(),
        last_login=last_login_dt.isoformat(),
        is_active=is_active,
        lifetime_value=lifetime_value,
        segment=segment,
        marketing_opt_in=bool(random.random() < 0.6),
        referral_source=referral_source,
        credit_score=credit_score,
        churn_risk_score=churn_risk,
    )


def generate_customer_records(count: int, seed: Optional[int] = None, locale: str = "en_US") -> Iterable[CustomerRecord]:
    """Generate an iterable of fabricated customer records.

    Args:
        count: Number of records to generate (>=0).
        seed: Optional random seed for deterministic output.
        locale: Faker locale string.
    """
    if count < 0:
        raise ValueError("count must be >= 0")
    if seed is not None:
        random.seed(seed)
        faker = Faker(locale)
        faker.seed_instance(seed)
    else:
        faker = Faker(locale)
    for _ in range(count):
        yield _generate_one(faker)


def generate_customers_csv(count: int, path: str | Path, seed: Optional[int] = None, locale: str = "en_US") -> Path:
    """Generate customers and write to CSV.

    Returns the output path.
    """
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    records = list(generate_customer_records(count=count, seed=seed, locale=locale))
    if not records:
        # still write header for empty dataset
        fieldnames = [f.name for f in CustomerRecord.__dataclass_fields__.values()]
        with out_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
        return out_path

    fieldnames = list(asdict(records[0]).keys())
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for r in records:
            writer.writerow(asdict(r))
    return out_path


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate fabricated customer data CSV")
    parser.add_argument("--count", "-c", type=int, required=True, help="Number of customer records to generate")
    parser.add_argument("--output", "-o", default="customers.csv", help="Output CSV file path (default: customers.csv)")
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed for reproducibility")
    parser.add_argument("--locale", default="en_US", help="Faker locale (default: en_US)")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        path = generate_customers_csv(count=args.count, path=args.output, seed=args.seed, locale=args.locale)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    print(f"Wrote {args.count} records to {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
