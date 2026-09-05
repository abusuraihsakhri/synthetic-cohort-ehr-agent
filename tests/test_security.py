"""
Security-focused tests for synthetic-cohort-ehr-agent.
Validates path traversal protection, input validation, and PHI guard enforcement.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from cli import _validate_file_path, _validate_identifier
from agents.base import PHIGuard, SecurityException, AuditTrail


class TestValidateFilePath:
    """Tests for path traversal protection."""

    def test_valid_relative_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        test_file = tmp_path / "test_input.csv"
        test_file.write_text("task_id,target\nT1,KEY-1\n")
        result = _validate_file_path("test_input.csv", must_exist=True)
        assert result.exists()

    def test_nonexistent_file_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(FileNotFoundError):
            _validate_file_path("nonexistent.csv", must_exist=True)

    def test_path_traversal_blocked(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError, match="within the working directory"):
            _validate_file_path("../etc/passwd", must_exist=False)

    def test_absolute_path_outside_cwd_blocked(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        outside = tmp_path.parent / "outside.csv"
        with pytest.raises(ValueError, match="within the working directory"):
            _validate_file_path(str(outside), must_exist=False)

    def test_output_path_within_cwd_allowed(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = _validate_file_path("output_results.csv", must_exist=False)
        assert result.name == "output_results.csv"

    def test_oversized_file_rejected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        large_file = tmp_path / "large.csv"
        # Write 11 MB file (exceeds 10 MB limit)
        large_file.write_bytes(b"x" * (11 * 1024 * 1024))
        with pytest.raises(ValueError, match="exceeds maximum"):
            _validate_file_path("large.csv", must_exist=True)


class TestValidateIdentifier:
    """Tests for identifier input validation."""

    def test_valid_identifier(self):
        result = _validate_identifier("TASK-2026-001", "task_id")
        assert result == "TASK-2026-001"

    def test_empty_identifier_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            _validate_identifier("", "task_id")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            _validate_identifier("   ", "task_id")

    def test_long_identifier_raises(self):
        with pytest.raises(ValueError, match="exceeds maximum length"):
            _validate_identifier("A" * 300, "task_id")

    def test_special_characters_blocked(self):
        with pytest.raises(ValueError, match="invalid characters"):
            _validate_identifier("task; rm -rf /", "task_id")

    def test_path_traversal_in_identifier_blocked(self):
        with pytest.raises(ValueError, match="invalid characters"):
            _validate_identifier("../../etc/passwd", "task_id")

    def test_sql_injection_pattern_blocked(self):
        with pytest.raises(ValueError, match="invalid characters"):
            _validate_identifier("1; DROP TABLE tasks", "task_id")


class TestPHIGuard:
    """Tests for PHI outbound guard enforcement."""

    def test_ssn_pattern_detected(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient SSN: 123-45-6789")

    def test_mrn_pattern_detected(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("MRN-994827 blood culture positive")

    def test_phone_number_detected(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Contact: 555-123-4567")

    def test_email_detected(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Email: patient@example.com")

    def test_clean_text_passes(self):
        PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")

    def test_redact_phi(self):
        result = PHIGuard.redact_phi("Patient MRN-12345 has SSN 123-45-6789")
        assert "REDACTED_IDENTIFIER" in result
        assert "MRN-12345" not in result
        assert "123-45-6789" not in result


class TestAuditTrail:
    """Tests for HMAC-SHA256 audit trail integrity."""

    def test_audit_trail_with_env_key(self, monkeypatch):
        monkeypatch.setenv("AUDIT_SECRET_KEY", "test-secret-key-for-unit-tests")
        trail = AuditTrail()
        entry = trail.log("test_actor", "test_tier", "TEST_EVENT", {"key": "value"})
        assert "current_hash" in entry
        assert entry["prev_hash"] == "GENESIS_BLOCK_0000000000000000"

    def test_audit_trail_chain_integrity(self, monkeypatch):
        monkeypatch.setenv("AUDIT_SECRET_KEY", "test-secret-key-for-unit-tests")
        trail = AuditTrail()
        trail.log("actor1", "tier1", "EVENT_1", {"data": 1})
        trail.log("actor2", "tier2", "EVENT_2", {"data": 2})
        trail.log("actor3", "tier3", "EVENT_3", {"data": 3})
        assert trail.verify_integrity() is True
        assert len(trail.get_trail()) == 3

    def test_audit_trail_tamper_detection(self, monkeypatch):
        monkeypatch.setenv("AUDIT_SECRET_KEY", "test-secret-key-for-unit-tests")
        trail = AuditTrail()
        trail.log("actor1", "tier1", "EVENT_1", {"data": 1})
        trail.log("actor2", "tier2", "EVENT_2", {"data": 2})
        # Tamper with the first entry
        trail.logs[0]["current_hash"] = "TAMPERED_HASH"
        assert trail.verify_integrity() is False

    def test_audit_trail_phi_blocked(self, monkeypatch):
        monkeypatch.setenv("AUDIT_SECRET_KEY", "test-secret-key-for-unit-tests")
        trail = AuditTrail()
        with pytest.raises(SecurityException):
            trail.log("actor", "tier", "EVENT", {"ssn": "123-45-6789"})
