"""
Command-Line Interface for SynthEHR Sentinel: Statistically Consistent Zero-PHI Synthetic Patient Cohort Generator.
"""
import argparse
import csv
import sys
from pathlib import Path
from .models import ClinicalCasePayload
from .agents import SynthEHRCoordinator

coordinator = SynthEHRCoordinator()

# Security: Maximum file size for batch processing (10 MB)
_MAX_BATCH_FILE_SIZE = 10 * 1024 * 1024


def _validate_safe_path(filepath: str, must_exist: bool = False) -> Path:
    """Validate file path for safe I/O, preventing path traversal."""
    path = Path(filepath).resolve()
    cwd = Path.cwd().resolve()
    if must_exist and not path.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")
    if must_exist and not path.is_file():
        raise ValueError(f"Path is not a regular file: {filepath}")
    if must_exist and path.stat().st_size > _MAX_BATCH_FILE_SIZE:
        raise ValueError(f"File exceeds maximum allowed size: {filepath}")
    try:
        path.relative_to(cwd)
    except ValueError:
        raise ValueError(f"File path must be within the working directory: {filepath}")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(prog="synthetic-cohort-ehr-agent", description="SynthEHR Sentinel: Statistically Consistent Zero-PHI Synthetic Patient Cohort Generator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit
    p_audit = subparsers.add_parser("audit", help="Run single case clinical audit")
    p_audit.add_argument("--case-id", default="CASE-2026-001")
    p_audit.add_argument("--primary", type=float, default=26.2)
    p_audit.add_argument("--secondary", type=float, default=12.5)
    p_audit.add_argument("--stat", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    # Chat
    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

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
        output = _validate_safe_path(args.output, must_exist=False)
        records = generate_cohort(
            count=args.count, seed=args.seed, age_min=args.age_min,
            age_max=args.age_max, female_fraction=args.female_fraction,
            max_encounters=args.max_encounters,
        )
        write_cohort(records, output)
        print(f"Generated {args.count} fictional patients, {len(records)} encounters -> {output}")
        return 0

    if args.command == "audit":
        case = ClinicalCasePayload(
            case_id=args.case_id,
            patient_synthetic_id="SYNTH-PT-881",
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_flag=args.status,
            is_stat=args.stat,
        )
        dossier = coordinator.process_case(case)
        print("=" * 80)
        print(f"  SYNTHEHR SENTINEL: STATISTICALLY CONSISTENT ZERO-PHI SYNTHETIC PATIENT COHORT GENERATOR")
        print(f"  Domain: Health Informatics | Standard: HL7 FHIR R4 & US Core Implementation Guide")
        print(f"  Case: {dossier['case_id']} | Status: [{dossier['overall_status']}] | Total Alerts: {dossier['total_alerts']}")
        print("=" * 80)
        for a in dossier["alerts"]:
            print(f"\n  [{a['urgency']}] from {a['sub_agent']}:")
            print(f"  Title: {a['title']}")
            print(f"  Finding: {a['clinical_finding']}")
            print(f"  Action: {a['actionable_recommendation']}")
        print("\n" + "=" * 80)
        return 0

    if args.command == "chat":
        ans = coordinator.query_supervisory_chat(" ".join(args.query))
        print(f"\n[SynthEHRCoordinator]:\n{ans}\n")
        return 0

    if args.command == "batch":
        in_path = _validate_safe_path(args.input, must_exist=True)
        out_path = _validate_safe_path(args.output, must_exist=False)

        with open(in_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)

        out_fields = fieldnames + ["overall_status", "total_alerts", "stat_critical_alerts", "consensus_summary"]
        out_rows = []
        for r in rows:
            try:
                case = ClinicalCasePayload(
                    case_id=str(r.get("case_id", "CASE-01"))[:64],
                    patient_synthetic_id=str(r.get("patient_synthetic_id", "SYNTH-01"))[:64],
                    primary_metric=float(r.get("metric_primary", r.get("primary_metric", 15.0))),
                    secondary_metric=float(r.get("metric_secondary", r.get("secondary_metric", 5.0))),
                    status_flag=str(r.get("status_flag", r.get("status_text", "NORMAL")))[:64],
                    is_stat=str(r.get("is_stat", r.get("critical_flag", ""))).lower() in ("true", "1", "yes"),
                )
            except (ValueError, TypeError) as e:
                print(f"Warning: Skipping malformed row: {e}", file=sys.stderr)
                continue
            dossier = coordinator.process_case(case)
            row_dict = dict(r)
            row_dict["overall_status"] = dossier["overall_status"]
            row_dict["total_alerts"] = dossier["total_alerts"]
            row_dict["stat_critical_alerts"] = dossier["stat_critical_alerts"]
            row_dict["consensus_summary"] = dossier["consensus_summary"]
            out_rows.append(row_dict)

        with open(out_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows(out_rows)
        print(f"Batch processed {len(out_rows)} records -> {args.output}")
        return 0

    if args.command == "serve":
        try:
            import uvicorn
            from .server import create_app
            app = create_app()
            if app:
                print(f"Starting SynthEHR Sentinel: Statistically Consistent Zero-PHI Synthetic Patient Cohort Generator on http://{args.host}:{args.port}")
                uvicorn.run(app, host=args.host, port=args.port)
        except ImportError:
            print("FastAPI / uvicorn not installed. Run 'pip install fastapi uvicorn'")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
