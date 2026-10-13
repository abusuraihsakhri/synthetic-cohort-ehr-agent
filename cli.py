"""
Command Line Interface for Synthetic Cohort Ehr Agent.
"""
import argparse
import csv
import re
import sys
from pathlib import Path
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from agents.base import AuditLogger

supervisor = SystemSupervisor(model_provider="mock")

# Security: Maximum file size for batch processing (10 MB)
MAX_BATCH_FILE_SIZE = 10 * 1024 * 1024


def _validate_file_path(filepath: str, must_exist: bool = False) -> Path:
    """Validate file path for safe I/O operations, preventing path traversal."""
    path = Path(filepath).resolve()
    cwd = Path.cwd().resolve()
    if must_exist and not path.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")
    if must_exist and not path.is_file():
        raise ValueError(f"Path is not a regular file: {filepath}")
    if must_exist and path.stat().st_size > MAX_BATCH_FILE_SIZE:
        raise ValueError(f"File exceeds maximum allowed size ({MAX_BATCH_FILE_SIZE} bytes): {filepath}")
    # Ensure path is within working directory (prevent path traversal)
    try:
        path.relative_to(cwd)
    except ValueError:
        raise ValueError(f"File path must be within the working directory: {filepath}")
    return path


def _validate_identifier(value: str, field_name: str) -> str:
    """Validate identifier fields to prevent injection attacks."""
    if not value or not value.strip():
        raise ValueError(f"{field_name} cannot be empty")
    if len(value) > 256:
        raise ValueError(f"{field_name} exceeds maximum length (256 characters)")
    # Allow common identifier patterns including UUIDs and task IDs
    if not re.match(r'^[A-Za-z0-9_\-:\.]+$', value):
        raise ValueError(f"{field_name} contains invalid characters: {value!r}")
    return value.strip()


def main(argv=None):
    parser = argparse.ArgumentParser(prog="synthetic-cohort-ehr-agent", description="Synthetic Cohort Ehr Agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit
    p_audit = subparsers.add_parser("audit", help="Run single task evaluation")
    p_audit.add_argument("--task-id", default="TASK-2026-001")
    p_audit.add_argument("--target", default="KEY-TARGET-01")
    p_audit.add_argument("--primary", type=float, default=28.5)
    p_audit.add_argument("--secondary", type=float, default=14.2)
    p_audit.add_argument("--critical", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    # Chat
    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    # Verify Audit
    subparsers.add_parser("verify-audit", help="Verify HMAC audit trail integrity")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    p_generate = subparsers.add_parser("generate", help="Create illustrative synthetic encounter rows")
    p_generate.add_argument("-n", "--count", type=int, default=100)
    p_generate.add_argument("--seed", type=int, default=42)
    p_generate.add_argument("--age-min", type=int, default=18)
    p_generate.add_argument("--age-max", type=int, default=85)
    p_generate.add_argument("--female-fraction", type=float, default=0.5)
    p_generate.add_argument("--max-encounters", type=int, default=2)
    p_generate.add_argument("-o", "--output", default="cohort.csv")

    args = parser.parse_args(argv)

    if args.command == "generate":
        from synthetic_cohort_ehr_agent.generator import generate_cohort, write_cohort
        output = _validate_file_path(args.output, must_exist=False)
        records = generate_cohort(
            count=args.count, seed=args.seed, age_min=args.age_min,
            age_max=args.age_max, female_fraction=args.female_fraction,
            max_encounters=args.max_encounters,
        )
        write_cohort(records, output)
        print(f"Generated {args.count} fictional patients, {len(records)} encounters -> {output}")
        return 0

    if args.command == "audit":
        task_id = _validate_identifier(args.task_id, "task_id")
        target = _validate_identifier(args.target, "target")
        status = _validate_identifier(args.status, "status")
        payload = SystemTaskPayload(
            task_id=task_id,
            target_identifier=target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=status,
            is_critical_flag=args.critical,
        )
        dossier = supervisor.process_task(payload)
        print("=" * 80)
        print(f"  SYNTHETIC COHORT EHR AGENT")
        print(f"  Domain: Clinical & Biomedical AI | Standard: CAP / CLSI / ISO Standards")
        print(f"  Dossier ID: {dossier.dossier_id} | Urgency: [{dossier.overall_urgency.value}]")
        print("=" * 80)
        for a in dossier.alerts:
            print(f"\n  [{a.urgency.value}] from {a.origin_worker}:")
            print(f"  Summary: {a.summary}")
            print(f"  Details: {a.technical_details}")
            print(f"  Action:  {a.actionable_remediation}")
        print(f"\n  HMAC-SHA256 Audit Hash: {dossier.audit_hash}")
        print("=" * 80)
        return 0

    if args.command == "chat":
        ans = supervisor.query_supervisory_chat(" ".join(args.query))
        print(f"\n[Synthetic Cohort Ehr Agent Supervisor]:\n{ans}\n")
        return 0

    if args.command == "verify-audit":
        trail = AuditLogger.get_trail()
        valid = AuditLogger.verify_integrity()
        print(f"Audit Trail Blocks: {len(trail)} | Cryptographic Integrity Verified: {valid}")
        return 0

    if args.command == "batch":
        in_path = _validate_file_path(args.input, must_exist=True)
        out_path = _validate_file_path(args.output, must_exist=False)

        with open(in_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)

        out_fields = fieldnames + ["overall_urgency", "integrity_status", "total_alerts", "audit_hash"]
        out_rows = []
        for r in rows:
            try:
                payload = SystemTaskPayload(
                    task_id=str(r.get("task_id", "TASK-01"))[:64],
                    target_identifier=str(r.get("target_identifier", "TARGET-01"))[:64],
                    primary_metric=float(r.get("primary_metric", 15.0)),
                    secondary_metric=float(r.get("secondary_metric", 5.0)),
                    status_descriptor=str(r.get("status_descriptor", "NOMINAL"))[:64],
                    is_critical_flag=str(r.get("is_critical_flag", "")).lower() in ("true", "1", "yes"),
                )
            except (ValueError, TypeError) as e:
                print(f"Warning: Skipping malformed row: {e}", file=sys.stderr)
                continue
            dossier = supervisor.process_task(payload)
            row_dict = dict(r)
            row_dict["overall_urgency"] = dossier.overall_urgency.value
            row_dict["integrity_status"] = dossier.integrity_status.value
            row_dict["total_alerts"] = dossier.total_alerts
            row_dict["audit_hash"] = dossier.audit_hash
            out_rows.append(row_dict)

        with open(out_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows(out_rows)
        print(f"Processed {len(out_rows)} records -> {args.output}")
        return 0

    if args.command == "serve":
        import uvicorn
        from agents.api import app
        print(f"Starting Synthetic Cohort Ehr Agent API server on http://{args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
