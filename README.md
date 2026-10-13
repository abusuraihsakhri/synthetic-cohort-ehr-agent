# Synthetic Cohort EHR Agent

An illustrative synthetic EHR encounter generator with a separate, rule-based metric audit. The browser demonstration runs entirely client-side; Python provides equivalent *types* of fictional encounter records, command-line exports, and a FastAPI service. The browser and Python implementations use different seeded random-number algorithms and are not byte-for-byte identical.

## What it provides

- **Synthetic cohort generator:** Produce 1–2,000 fictional patients, each with 1–5 dated encounters, synthetic identifiers, age, assigned sex, BMI, blood pressure, heart rate, creatinine, and a clearly labelled example systolic flag. Supply a random seed for repeatability.
- **Browser app:** Local generator, encounter preview, CSV/JSON download, and independent rule-based audit demonstration; no server required.
- **Python CLI/API:** Cohort generation, CSV/JSON exports and an existing multi-worker metric audit. The root CLI additionally supports batch audit, chat mock, audit verification and HTTP server commands.
- **Audit model:** Example rules flag a primary metric above 25, a secondary metric above 12 or a critical flag, and selected anomaly keywords. These thresholds are **demonstration rules**, not validated clinical cutoffs.
- **In-memory audit ledger:** HMAC-SHA256 chaining with signature verification. Ledger entries are lost on restart; a persistent, authenticated, regulatory audit trail is **not** provided.

## Use in the browser

Open `web/index.html` locally or use the published GitHub Pages site when available. The page does not fetch APIs, upload data or require Python, Pyodide, or external JavaScript dependencies. Generated data exists only in the current tab until it is downloaded.

## Python installation

Requires Python 3.10–3.12 for the tested CI matrix. From the repository root:

```bash
python -m pip install -e ".[server,test]"
python cli.py generate --count 100 --seed 42 --age-min 18 --age-max 85 --max-encounters 2 -o cohort.csv
python cli.py generate -n 10 --seed 7 -o cohort.json
```

The installed package command is also available:

```bash
synthetic-cohort-ehr-engine generate -n 20 --seed 42 -o cohort.csv
```

Run the pre-existing metric audit and API:

```bash
python cli.py audit --task-id DEMO-001 --target SYN-001 --primary 29.4 --secondary 14.8 --critical --status DISCORDANT
python cli.py batch -i sample.csv -o results.csv
python cli.py serve --host 127.0.0.1 --port 8000
```

Visit `http://127.0.0.1:8000/docs` for FastAPI's interactive API schema. `POST /api/cohort` accepts JSON such as:

```json
{"count": 20, "seed": 42, "age_min": 18, "age_max": 85, "female_fraction": 0.5, "max_encounters": 2}
```

Other endpoints include `POST /api/audit`, `POST /api/chat`, `GET /api/audit/logs`, `GET /health`, and `GET /metrics`. The `agents/` audit implementation, `synthetic_cohort_ehr_agent/` package CLI, and older `synth_ehr_sentinel.py` prototype are retained for compatibility; they expose different audit input schemas.

## Privacy, research validity and security limitations

This tool **does not contain, anonymize or validate real patient records**. The generators use manually specified distributions and simplified correlations, not a fitted clinical population model. The output is not suitable for clinical decision-making, statistical inference about real populations, or claims of privacy-safe release. The PHI-pattern guard on the Python audit path is a limited heuristic and **does not establish HIPAA Safe Harbor compliance**. Do not supply identifiable patient information.

The browser requires no remote services and does not persist records in local storage. The Python API operates in the server process; do not publicly expose it without appropriate authentication, TLS, rate limiting and data-handling controls. Audit verification is process-local and requires a stable secret for any same-process audit checks.

For Docker, provide an externally generated key rather than hard-coding a deployment secret:

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up --build
```

## Tests and development

```bash
python -m pip install -e ".[server,test]"
python -m pytest -q
node --test tests_js/*.test.cjs
node --check web/engine.js
node --check web/app.js
```

GitHub Actions tests Python 3.10, 3.11, 3.12, checks the browser engine with Node, and gates a static Pages deployment on success. The browser UI targets modern evergreen browsers; automated cross-browser UI testing is not included.

## License

[MIT](LICENSE).
