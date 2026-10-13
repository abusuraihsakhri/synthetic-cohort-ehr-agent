"""Regression coverage for illustrative synthetic cohort generation and audit security."""
import csv
import json
import math

import pytest
from fastapi.testclient import TestClient

from agents.api import app
from agents.base import AuditTrail
from cli import main as root_main
from synthetic_cohort_ehr_agent.cli import main as package_main
from synthetic_cohort_ehr_agent.generator import FIELDS, generate_cohort, write_cohort


def test_deterministic_cohort_and_consistent_encounters():
    first = generate_cohort(count=30, seed=9, age_min=30, age_max=40, max_encounters=3)
    second = generate_cohort(count=30, seed=9, age_min=30, age_max=40, max_encounters=3)
    assert first == second
    assert len({r["patient_id"] for r in first}) == 30
    assert len({r["encounter_id"] for r in first}) == len(first)
    assert len(first) <= 90
    subjects = {}
    for row in first:
        assert 30 <= row["age_years"] <= 40
        assert 75 <= row["systolic_bp_mm_hg"] <= 220
        assert set(row) == set(FIELDS)
        signature = (row["age_years"], row["sex"], row["bmi_kg_m2"])
        if row["patient_id"] in subjects:
            assert subjects[row["patient_id"]] == signature
        subjects[row["patient_id"]] = signature


@pytest.mark.parametrize("kwargs", [
    {"count": 0}, {"count": 2001}, {"seed": -1},
    {"age_min": 70, "age_max": 20}, {"female_fraction": float("nan")},
    {"max_encounters": 6}, {"count": True},
])
def test_cohort_rejects_invalid_arguments(kwargs):
    with pytest.raises(ValueError):
        generate_cohort(**kwargs)


def test_csv_json_export_and_cli(tmp_path, monkeypatch):
    records = generate_cohort(count=2, seed=1)
    csv_path = tmp_path / "cohort.csv"
    json_path = tmp_path / "cohort.json"
    write_cohort(records, csv_path)
    write_cohort(records, json_path)
    with csv_path.open(newline="", encoding="utf-8") as stream:
        assert len(list(csv.DictReader(stream))) == len(records)
    assert json.loads(json_path.read_text(encoding="utf-8")) == records
    monkeypatch.chdir(tmp_path)
    assert root_main(["generate", "-n", "2", "--seed", "1", "-o", "root.csv"]) == 0
    assert package_main(["generate", "-n", "2", "--seed", "1", "-o", "package.csv"]) == 0
    assert (tmp_path / "root.csv").exists()
    assert (tmp_path / "package.csv").exists()


def test_api_cohort_and_input_validation():
    client = TestClient(app)
    response = client.post("/api/cohort", json={"count": 3, "seed": 77})
    assert response.status_code == 200
    body = response.json()
    assert body["patients"] == 3
    assert len({r["patient_id"] for r in body["records"]}) == 3
    assert client.post("/api/cohort", json={"count": 2001}).status_code == 422
    assert client.post("/api/cohort", json={"age_min": 70, "age_max": 20}).status_code == 422
    assert client.post("/api/audit", json={
        "task_id": "T1", "target_identifier": "TARGET-01",
        "primary_metric": "NaN", "secondary_metric": 1,
    }).status_code == 422
    assert client.post("/api/audit", json={
        "task_id": "T1", "target_identifier": "MRN-123456",
        "primary_metric": 1,
    }).status_code == 422


def test_audit_hmac_verifies_each_entry_not_just_chain_links():
    trail = AuditTrail(secret_key="test-secret")
    trail.log("actor", "tier", "event", {"value": "safe"})
    assert trail.verify_integrity()
    exported = trail.get_trail()
    exported[0]["event_type"] = "fake"
    assert trail.verify_integrity()
    trail.logs[0]["event_type"] = "fake"
    assert not trail.verify_integrity()


def test_audit_hmac_detects_last_entry_tampering():
    trail = AuditTrail(secret_key="test-secret")
    trail.log("actor", "tier", "event", {"value": 1})
    trail.log("actor", "tier", "event", {"value": 2})
    trail.logs[-1]["payload_hash"] = "0" * 64
    assert not trail.verify_integrity()
