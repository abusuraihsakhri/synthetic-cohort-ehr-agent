# Synthetic Cohort Ehr Agent

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Synthetic Cohort Ehr Agent** is an advanced analytical and computational platform implementing Multivariate-Correlated Zero-PHI Synthetic Patient Cohort Generator. It provides multi-agent clinical decision support with tamper-evident audit trails and PHI outbound protection.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`Severity`** — dedicated module for severity evaluation and state verification.
- **`DomainKnowledgeRegistry`**: Enterprise domain rules, guideline matrices, and evidence benchmarks.
- **`AgentAlert`** — dedicated module for agent alert evaluation and state verification.
- **`DemographicDistributionAgent`**: Specialized Sub-Agent 1 for synthetic-cohort-ehr-agent
- **`ClinicalTrajectoryGeneratorAgent`**: Specialized Sub-Agent 2 for synthetic-cohort-ehr-agent
- **`CorrelationPreserverAgent`**: Specialized Sub-Agent 3 for synthetic-cohort-ehr-agent

---

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/synthetic-cohort-ehr-agent.git
cd synthetic-cohort-ehr-agent

# Install dependencies
pip install fastapi uvicorn pydantic pytest

# Optional: Set audit secret key (recommended for production)
export AUDIT_SECRET_KEY="your-secure-random-key-here"
```

---

## 💻 CLI Quickstart & Usage

### 1. Run Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. Query the Supervisory Chat
```bash
python cli.py chat "What is the system status?"
```

### 3. Batch Process CSV Records
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch FastAPI REST Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### CLI Commands Reference

| Command | Description | Key Arguments |
|:--------|:------------|:--------------|
| `audit` | Run single task evaluation | `--task-id`, `--target`, `--primary`, `--secondary`, `--critical`, `--status` |
| `chat` | System configuration query | `query` (positional) |
| `batch` | Batch process CSV records | `-i/--input`, `-o/--output` |
| `verify-audit` | Verify HMAC audit trail integrity | — |
| `serve` | Launch FastAPI REST server | `--host`, `--port` |

### Input Data Schema (for batch processing)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `task_id` | Unique task / case identifier | Required |
| `target_identifier` | Entity or target key | Required |
| `primary_metric` | Primary measurement or score | Required |
| `secondary_metric` | Secondary kinetic or confidence score | Optional (default: 0.0) |
| `status_descriptor` | Status code or phenotype descriptor | Optional (default: "NOMINAL") |
| `is_critical_flag` | Emergency escalation flag | Optional (default: false) |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Path Traversal Protection:** All file I/O operations validate paths to prevent directory traversal attacks.
* **Input Validation:** Identifier fields are validated against injection patterns and length limits.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Security Configuration

Set the `AUDIT_SECRET_KEY` environment variable to a secure random value for production deployments. Without it, a runtime warning is issued and a random key is generated per session.

```bash
# Generate a secure key
python -c "import secrets; print(secrets.token_hex(32))"

# Set it
export AUDIT_SECRET_KEY="your-generated-key"
```

---

## 🧪 Testing & Verification

Run the complete test suite:

```bash
pytest -v
```

Run specific test modules:

```bash
pytest tests/test_security.py -v          # Security-focused tests
pytest tests/test_synthetic_cohort_ehr_agent_package.py -v  # Package module tests
pytest test_synth_ehr_sentinel.py -v      # Sentinel integration tests
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t synthetic-cohort-ehr-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY="your-secure-key" synthetic-cohort-ehr-agent
```

Or using Docker Compose:

```bash
docker-compose up -d
```

---

## 📁 Project Structure

```
synthetic-cohort-ehr-agent/
├── agents/                          # Core agent modules (FastAPI-based)
│   ├── api.py                       # FastAPI REST endpoints
│   ├── base.py                      # Security, PHI guard, audit trail
│   ├── models.py                    # Pydantic data models
│   ├── supervisor.py                # Multi-agent orchestrator
│   ├── workers.py                   # Specialized evaluation workers
│   ├── llm_factory.py               # LLM provider abstraction
│   ├── metrics.py                   # Prometheus metrics
│   ├── learning.py                  # Bayesian calibration engine
│   └── streamer.py                  # WebSocket telemetry
├── synthetic_cohort_ehr_agent/      # Alternative package implementation
│   ├── agents.py                    # Coordinator and sub-agents
│   ├── engine.py                    # Clinical domain rules
│   ├── models.py                    # Data models
│   ├── cli.py                       # Package CLI
│   └── server.py                    # FastAPI application
├── tests/                           # Test suite
│   ├── test_security.py             # Security validation tests
│   ├── test_synthetic_cohort_ehr_agent.py  # Core agent tests
│   ├── test_synthetic_cohort_ehr_agent_package.py  # Package tests
│   └── test_enrichment.py           # Enrichment module tests
├── cli.py                           # Main CLI entry point
├── synth_ehr_sentinel.py            # Sentinel implementation
├── enrichment.py                    # Feature enrichment engines
├── simulator.py                     # Load testing simulator
├── Dockerfile                       # Container definition
├── docker-compose.yml               # Compose configuration
└── pyproject.toml                   # Project metadata
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
