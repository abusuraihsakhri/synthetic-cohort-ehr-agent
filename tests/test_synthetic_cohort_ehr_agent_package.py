"""
Automated Pytest for synthetic_cohort_ehr_agent package modules.
Domain: Health Informatics
Standard: HL7 FHIR R4 & US Core Implementation Guide
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from synthetic_cohort_ehr_agent.models import (
    ClinicalCasePayload,
    AgentAlert,
    UrgencyLevel,
    ClinicalIntegrityStatus,
)
from synthetic_cohort_ehr_agent.agents import (
    SynthEHRCoordinator,
    DemographicDistributionAgent,
    ClinicalTrajectoryGeneratorAgent,
    CorrelationPreserverAgent,
)
from synthetic_cohort_ehr_agent.engine import ClinicalDomainEngine
from synthetic_cohort_ehr_agent.cli import main


def test_clinical_case_payload_creation():
    case = ClinicalCasePayload(
        case_id="CASE-001",
        patient_synthetic_id="SYNTH-PT-001",
        primary_metric=15.0,
        secondary_metric=5.0,
        status_flag="NORMAL",
    )
    assert case.case_id == "CASE-001"
    assert case.is_stat is False
    assert case.biomarkers == {}


def test_clinical_domain_engine_primary_index():
    # Below threshold - no alert
    result = ClinicalDomainEngine.evaluate_primary_index(15.0)
    assert result is None

    # Above threshold - alert
    result = ClinicalDomainEngine.evaluate_primary_index(25.0)
    assert result is not None
    assert "exceeds" in result["finding"]


def test_clinical_domain_engine_secondary_kinetics():
    # Below threshold, not stat
    result = ClinicalDomainEngine.evaluate_secondary_kinetics(5.0, False)
    assert result is None

    # Above threshold
    result = ClinicalDomainEngine.evaluate_secondary_kinetics(15.0, False)
    assert result is not None

    # STAT flag
    result = ClinicalDomainEngine.evaluate_secondary_kinetics(5.0, True)
    assert result is not None


def test_clinical_domain_engine_biomarker_concordance():
    # Normal status
    result = ClinicalDomainEngine.evaluate_biomarker_concordance("NORMAL", {})
    assert result is None

    # Discordant status
    result = ClinicalDomainEngine.evaluate_biomarker_concordance("DISCORDANT", {})
    assert result is not None

    # Equivocal status
    result = ClinicalDomainEngine.evaluate_biomarker_concordance("EQUIVOCAL", {})
    assert result is not None


def test_demographic_distribution_agent():
    agent = DemographicDistributionAgent()
    # Below threshold
    alerts = agent.audit(ClinicalCasePayload(
        case_id="C1", patient_synthetic_id="P1",
        primary_metric=10.0, secondary_metric=5.0, status_flag="NORMAL",
    ))
    assert len(alerts) == 0

    # Above threshold
    alerts = agent.audit(ClinicalCasePayload(
        case_id="C2", patient_synthetic_id="P2",
        primary_metric=25.0, secondary_metric=5.0, status_flag="NORMAL",
    ))
    assert len(alerts) == 1
    assert alerts[0].urgency == UrgencyLevel.WARNING


def test_clinical_trajectory_generator_agent():
    agent = ClinicalTrajectoryGeneratorAgent()
    # Normal
    alerts = agent.audit(ClinicalCasePayload(
        case_id="C1", patient_synthetic_id="P1",
        primary_metric=10.0, secondary_metric=5.0, status_flag="NORMAL",
    ))
    assert len(alerts) == 0

    # STAT
    alerts = agent.audit(ClinicalCasePayload(
        case_id="C2", patient_synthetic_id="P2",
        primary_metric=10.0, secondary_metric=5.0, status_flag="NORMAL", is_stat=True,
    ))
    assert len(alerts) == 1
    assert alerts[0].urgency == UrgencyLevel.STAT_CRITICAL


def test_correlation_preserver_agent():
    agent = CorrelationPreserverAgent()
    # Normal
    alerts = agent.audit(ClinicalCasePayload(
        case_id="C1", patient_synthetic_id="P1",
        primary_metric=10.0, secondary_metric=5.0, status_flag="NORMAL",
    ))
    assert len(alerts) == 0

    # Discordant
    alerts = agent.audit(ClinicalCasePayload(
        case_id="C2", patient_synthetic_id="P2",
        primary_metric=10.0, secondary_metric=5.0, status_flag="DISCORDANT",
    ))
    assert len(alerts) == 1
    assert alerts[0].urgency == UrgencyLevel.ADVISORY


def test_coordinator_process_case():
    coord = SynthEHRCoordinator()
    # Normal case
    dossier = coord.process_case(ClinicalCasePayload(
        case_id="CASE-NORMAL",
        patient_synthetic_id="SYNTH-001",
        primary_metric=10.0,
        secondary_metric=5.0,
        status_flag="NORMAL",
    ))
    assert dossier["overall_status"] == ClinicalIntegrityStatus.CONCORDANT_NORMAL.value
    assert dossier["total_alerts"] == 0

    # Critical case
    dossier = coord.process_case(ClinicalCasePayload(
        case_id="CASE-CRITICAL",
        patient_synthetic_id="SYNTH-002",
        primary_metric=30.0,
        secondary_metric=15.0,
        status_flag="DISCORDANT",
        is_stat=True,
    ))
    assert dossier["overall_status"] == ClinicalIntegrityStatus.CRITICAL_ACTION_REQUIRED.value
    assert dossier["stat_critical_alerts"] > 0


def test_coordinator_query_supervisory_chat():
    coord = SynthEHRCoordinator()
    response = coord.query_supervisory_chat("What is the status?")
    assert "tracking" in response or "cases" in response

    response = coord.query_supervisory_chat("Tell me about guidelines")
    assert "HL7" in response or "standard" in response


def test_cli_audit_command():
    assert main(["audit", "--case-id", "CLI-TEST-01"]) == 0


def test_cli_chat_command():
    assert main(["chat", "What", "is", "the", "status?"]) == 0


def test_agent_alert_to_dict():
    alert = AgentAlert(
        alert_id="TEST-001",
        sub_agent="TestAgent",
        urgency=UrgencyLevel.WARNING,
        title="Test Alert",
        clinical_finding="Test finding",
        actionable_recommendation="Test recommendation",
    )
    d = alert.to_dict()
    assert d["alert_id"] == "TEST-001"
    assert d["urgency"] == "WARNING"
    assert "timestamp" in d
