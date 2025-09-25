from __future__ import annotations

import csv
import random
import uuid
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta, UTC
from pathlib import Path
from typing import Iterable, Optional

from faker import Faker

INSURANCE_PROVIDERS = [
    "Aetna",
    "Blue Cross",
    "United Healthcare",
    "Cigna",
    "Kaiser",
    "Medicare",
    "Medicaid",
]
SMOKING_STATUS = ["Never", "Former", "Current"]
BLOOD_TYPES = [
    "O+","O-","A+","A-","B+","B-","AB+","AB-"
]
CHRONIC_CONDITIONS = [
    "Hypertension",
    "Diabetes Type 2",
    "Asthma",
    "Hyperlipidemia",
    "Depression",
    "Coronary Artery Disease",
    "COPD",
    "Arthritis",
    "CKD Stage 2",
    "Obesity",
]
ALLERGIES = [
    "Penicillin",
    "Latex",
    "Peanuts",
    "Shellfish",
    "NSAIDs",
    "Pollen",
    "Dust",
]
MEDICATIONS = [
    "Metformin",
    "Lisinopril",
    "Atorvastatin",
    "Albuterol",
    "Levothyroxine",
    "Omeprazole",
    "Amlodipine",
]


@dataclass
class PatientRecord:
    patient_id: str
    first_name: str
    last_name: str
    gender: str
    date_of_birth: str
    email: str
    phone: str
    street_address: str
    city: str
    state: str
    postal_code: str
    country: str
    medical_record_number: str
    insurance_provider: str
    insurance_plan: str
    primary_physician: str
    blood_type: str
    height_cm: int
    weight_kg: int
    bmi: float
    smoking_status: str
    chronic_conditions: str
    allergies: str
    medications_current: str
    last_visit_date: str
    next_appointment_date: str
    risk_score: float
    emergency_contact_name: str
    emergency_contact_phone: str


def _deterministic_uuid(seed: int, idx: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"patient:{seed}:{idx}"))


def _random_dob(faker: Faker) -> date:
    # Ages 0 - 100
    today = date.today()
    start = today - timedelta(days=365 * 100)
    end = today
    delta = (end - start).days
    return start + timedelta(days=faker.random_int(min=0, max=delta))


def _compute_bmi(height_cm: int, weight_kg: int) -> float:
    h_m = height_cm / 100.0
    return round(weight_kg / (h_m * h_m), 1)


def _risk_score(age: int, bmi: float, cond_count: int, smoking: str) -> float:
    score = 0.1
    score += min(0.3, age / 200)  # age factor
    if bmi >= 30:
        score += 0.15
    elif bmi >= 25:
        score += 0.07
    score += min(0.25, cond_count * 0.06)
    if smoking == "Current":
        score += 0.2
    elif smoking == "Former":
        score += 0.05
    score += random.uniform(-0.03, 0.03)
    return round(max(0.0, min(1.0, score)), 3)


def generate_patient_records(count: int, seed: Optional[int] = None, locale: str = "en_US") -> Iterable[PatientRecord]:
    if count < 0:
        raise ValueError("count must be >= 0")
    if seed is not None:
        random.seed(seed)
        faker = Faker(locale)
        faker.seed_instance(seed)
    else:
        faker = Faker(locale)
    today = datetime.now(UTC)
    for i in range(count):
        patient_id = _deterministic_uuid(seed, i) if seed is not None else str(uuid.uuid4())
        first_name = faker.first_name()
        last_name = faker.last_name()
        gender = random.choice(["Male","Female","Other"])  # simplistic
        dob = _random_dob(faker)
        age = (date.today() - dob).days // 365
        email = f"{first_name.lower()}.{last_name.lower()}@{faker.free_email_domain()}".replace("'", "")
        phone = faker.phone_number()
        address = faker.street_address().replace("\n", ", ")
        city = faker.city()
        state = faker.state_abbr() if hasattr(faker, "state_abbr") else faker.state()
        postal_code = faker.postcode()
        country = faker.current_country() if hasattr(faker, "current_country") else faker.country()
        mrn = f"MRN{faker.random_number(digits=8):08d}"
        ins_provider = random.choice(INSURANCE_PROVIDERS)
        ins_plan = random.choice(["Bronze","Silver","Gold","Platinum","HMO","PPO"])
        physician = f"Dr. {faker.first_name()} {faker.last_name()}"
        blood_type = random.choice(BLOOD_TYPES)
        height_cm = int(min(205, max(140, random.gauss(170, 10))))
        weight_kg = int(min(180, max(40, random.gauss(75, 15))))
        bmi = _compute_bmi(height_cm, weight_kg)
        smoking_status = random.choices(SMOKING_STATUS, weights=[0.6,0.25,0.15], k=1)[0]
        cond_sample = random.sample(CHRONIC_CONDITIONS, k=random.randint(0, min(4, len(CHRONIC_CONDITIONS))))
        allergies_sample = random.sample(ALLERGIES, k=random.randint(0, 3))
        meds_sample = random.sample(MEDICATIONS, k=random.randint(0, 4))
        last_visit = faker.date_time_between(start_date=today - timedelta(days=365), end_date=today)
        if random.random() < 0.7:
            next_appt = faker.date_time_between(start_date=today, end_date=today + timedelta(days=180))
            next_appt_str = next_appt.isoformat()
        else:
            next_appt_str = ""
        risk = _risk_score(age, bmi, len(cond_sample), smoking_status)
        emergency_name = f"{faker.first_name()} {faker.last_name()}"
        emergency_phone = faker.phone_number()
        yield PatientRecord(
            patient_id=patient_id,
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            date_of_birth=dob.isoformat(),
            email=email,
            phone=phone,
            street_address=address,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            medical_record_number=mrn,
            insurance_provider=ins_provider,
            insurance_plan=ins_plan,
            primary_physician=physician,
            blood_type=blood_type,
            height_cm=height_cm,
            weight_kg=weight_kg,
            bmi=bmi,
            smoking_status=smoking_status,
            chronic_conditions=";".join(cond_sample),
            allergies=";".join(allergies_sample),
            medications_current=";".join(meds_sample),
            last_visit_date=last_visit.isoformat(),
            next_appointment_date=next_appt_str,
            risk_score=risk,
            emergency_contact_name=emergency_name,
            emergency_contact_phone=emergency_phone,
        )


def generate_patients_csv(count: int, path: str | Path, seed: Optional[int] = None, locale: str = "en_US") -> Path:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(PatientRecord.__annotations__.keys())
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for rec in generate_patient_records(count=count, seed=seed, locale=locale):
            writer.writerow(asdict(rec))
    return out_path
