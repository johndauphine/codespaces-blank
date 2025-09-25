from __future__ import annotations

import csv
import random
import uuid
import hashlib
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta, UTC
from pathlib import Path
from typing import Iterable, Optional

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
    delta_days = (end - start).days
    return start + timedelta(days=faker.random_int(min=0, max=delta_days))


def _generate_one(faker: Faker, customer_id: str) -> CustomerRecord:
    dob = _random_date(
        faker,
        date(1940, 1, 1),
        date(2005, 12, 31),
    )
    now = datetime.now(UTC)
    signup_start = now - timedelta(days=5 * 365)
    signup_dt = faker.date_time_between(start_date=signup_start, end_date=now)
    if faker.random.random() < 0.8:
        last_login_dt = faker.date_time_between(start_date=signup_dt, end_date=now)
        is_active = True
    else:
        last_login_dt = signup_dt + timedelta(hours=faker.random_int(min=0, max=72))
        is_active = False
    lifetime_value = round(random.gammavariate(2.5, 120), 2)
    segment = random.choices(
        SEGMENTS,
        weights=[0.15, 0.25, 0.45, 0.05, 0.10],
        k=1,
    )[0]
    referral_source = random.choice(REFERRAL_SOURCES)
    credit_score = int(min(850, max(300, random.gauss(690, 60))))
    base_risk = 0.5
    if is_active:
        base_risk -= 0.15
    if segment == "Enterprise":
        base_risk -= 0.10
    elif segment == "Consumer":
        base_risk += 0.05
    base_risk -= min(0.20, lifetime_value / 10000)
    base_risk += random.uniform(-0.05, 0.05)
    churn_risk = round(min(1.0, max(0.0, base_risk)), 3)
    first_name = faker.first_name()
    last_name = faker.last_name()
    domain = faker.free_email_domain()
    email = f"{first_name.lower()}.{last_name.lower()}@{domain}".replace("'", "")
    return CustomerRecord(
        customer_id=customer_id,
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


def _deterministic_uuid(seed: int, idx: int) -> str:
    # Use uuid5 for stable, namespaced deterministic UUID based on seed and index
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"customer:{seed}:{idx}"))


def generate_customer_records(count: int, seed: Optional[int] = None, locale: str = "en_US") -> Iterable[CustomerRecord]:
    if count < 0:
        raise ValueError("count must be >= 0")
    if seed is not None:
        random.seed(seed)
        faker = Faker(locale)
        faker.seed_instance(seed)
    else:
        faker = Faker(locale)
    for i in range(count):
        if seed is not None:
            cid = _deterministic_uuid(seed, i)
        else:
            cid = str(uuid.uuid4())
        yield _generate_one(faker, cid)


def generate_customers_csv(count: int, path: str | Path, seed: Optional[int] = None, locale: str = "en_US") -> Path:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [f for f in CustomerRecord.__annotations__.keys()]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for record in generate_customer_records(count=count, seed=seed, locale=locale):
            writer.writerow(asdict(record))
    return out_path
