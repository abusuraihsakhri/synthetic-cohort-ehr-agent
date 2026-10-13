"""Deterministic illustrative synthetic EHR encounter records.

This generator samples artificial records from simple, documented distributions.
It is not fitted to real patient data, privacy certified, or clinically validated.
"""
from __future__ import annotations

import csv
import json
import math
import random
from datetime import date, timedelta
from pathlib import Path


FIELDS = (
    "patient_id", "encounter_id", "encounter_date", "age_years", "sex",
    "bmi_kg_m2", "systolic_bp_mm_hg", "diastolic_bp_mm_hg",
    "heart_rate_bpm", "creatinine_mg_dl", "bp_flag",
)


def generate_cohort(
    count: int = 100, seed: int = 42, age_min: int = 18, age_max: int = 85,
    female_fraction: float = 0.5, max_encounters: int = 2,
) -> list[dict]:
    """Return encounter rows; all values are fictional and non-identifying.

    Blood pressure is loosely dependent on age and BMI to illustrate
    non-independent variables. These are *not* population-based models.
    """
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 2000:
        raise ValueError("count must be an integer between 1 and 2000")
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 4294967295:
        raise ValueError("seed must be an integer between 0 and 2^32-1")
    if not (
        isinstance(age_min, int) and not isinstance(age_min, bool)
        and isinstance(age_max, int) and not isinstance(age_max, bool)
        and 0 <= age_min <= age_max <= 110
    ):
        raise ValueError("age range must satisfy 0 <= min <= max <= 110")
    if not isinstance(female_fraction, (int, float)) or isinstance(female_fraction, bool) or (
        not math.isfinite(female_fraction) or not 0 <= female_fraction <= 1
    ):
        raise ValueError("female_fraction must be finite and between 0 and 1")
    if isinstance(max_encounters, bool) or not isinstance(max_encounters, int) or not 1 <= max_encounters <= 5:
        raise ValueError("max_encounters must be an integer between 1 and 5")

    rng = random.Random(seed)
    records: list[dict] = []
    anchor = date(2025, 1, 1)
    for i in range(count):
        patient_id = f"SYN-{seed:08X}-{i + 1:05d}"
        age = rng.randint(age_min, age_max)
        sex = "F" if rng.random() < female_fraction else "M"
        bmi = round(max(14, min(48, rng.gauss(26, 4.5))), 1)
        creatinine_base = 0.72 if sex == "F" else 0.90
        first_day = rng.randint(0, 280)
        encounters = rng.randint(1, max_encounters)
        for j in range(encounters):
            systolic = round(max(75, min(220, rng.gauss(105 + 0.43 * age + 0.65 * (bmi - 25), 12))))
            diastolic = round(max(40, min(135, rng.gauss(69 + 0.16 * age + 0.2 * (bmi - 25), 8))))
            heart_rate = round(max(40, min(150, rng.gauss(74, 11))))
            creatinine = round(max(0.3, min(4.0, rng.gauss(creatinine_base + 0.002 * age, 0.17))), 2)
            records.append({
                "patient_id": patient_id,
                "encounter_id": f"{patient_id}-E{j + 1}",
                "encounter_date": (anchor + timedelta(days=first_day + j * 21)).isoformat(),
                "age_years": age,
                "sex": sex,
                "bmi_kg_m2": bmi,
                "systolic_bp_mm_hg": systolic,
                "diastolic_bp_mm_hg": diastolic,
                "heart_rate_bpm": heart_rate,
                "creatinine_mg_dl": creatinine,
                "bp_flag": "elevated_systolic_example" if systolic >= 140 else "none",
            })
    return records


def write_cohort(records: list[dict], destination: str | Path) -> None:
    """Export as UTF-8 CSV or JSON according to the file extension."""
    path = Path(destination)
    if path.suffix.lower() == ".json":
        with path.open("w", encoding="utf-8") as stream:
            json.dump(records, stream, indent=2)
            stream.write("\n")
    elif path.suffix.lower() == ".csv":
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(records)
    else:
        raise ValueError("Output file must end in .csv or .json")
