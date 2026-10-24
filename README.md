# Celesto Agent Flight Recorder

A containerized FastAPI service for recording agent execution runs, maintaining a persistent run ledger, and capturing command audit evidence for sandbox-based agent workflows.

## Problem statement

Agent workflows need reliable execution records, traceable command decisions, and consistent state management. Without a centralized record of execution, it becomes difficult to investigate failures, verify sandbox activity, and understand what happened during an agent run.

Celesto Agent Flight Recorder addresses this problem by providing an API for run registration and retrieval, a PostgreSQL-backed ledger, and structured command-audit records. The service is designed to support traceability, validation, and evidence-driven verification of agent execution.

## Objectives

- Record and retrieve agent execution runs through a REST API.
- Persist run information using PostgreSQL.
- Validate sandbox names, execution states, and execution targets.
- Record command decisions in structured JSON Lines format.
- Support reproducible local deployment using Docker Compose.
- Organize reliability, containment, capability, and failure-policy evidence as project reports.

## Technology stack

- **Python** — application logic
- **FastAPI** — REST API and request validation
- **PostgreSQL** — persistent execution ledger
- **Docker and Docker Compose** — containerized deployment
- **Pytest** — automated testing
- **Celesto SDK** — integration with Celesto computer/sandbox workflows

## Architecture

The application consists of the following components:

1. **API service:** Accepts requests, validates execution records, and exposes health and run endpoints.
2. **PostgreSQL ledger:** Stores execution-run records persistently.
3. **Celesto integration:** Provides the integration point for attaching to a configured Celesto computer and executing permitted commands.
4. **Command audit log:** Stores structured command records, decisions, timestamps, sandbox names, and execution targets.
5. **Verification reports:** Hold project evidence for capabilities, reliability, lifecycle, containment, and failure-policy checks.

```text
Client
  |
  v
FastAPI service (:8080)
  |                 |
  v                 v
PostgreSQL       Celesto integration
ledger           and command execution
  |                 |
  v                 v
Run records      Command audit log
                    |
                    v
              Verification reports
```

## Repository structure

```text
celesto_agent_flight_recorder/
├── app/
│   ├── main.py
│   ├── ledger.py
│   ├── celesto_executor.py
│   └── agent.py
├── logs/
│   └── commands.jsonl
├── reports/
│   ├── problem.json
│   ├── capabilities.json
│   ├── lifecycle.json
│   ├── reliability.json
│   ├── postmortem.md
│   ├── containment.json
│   ├── failure_policy.json
│   ├── failure_trace.jsonl
│   └── concurrency.json
├── scripts/
│   └── verify.py
├── seeds/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

*The tree above describes the expected organization. Confirm that every listed file exists in the submitted repository.*

## Setup

### Prerequisites

- Docker Desktop with Docker Compose support
- Git
- A Celesto account and API key if running live cloud integration
- The required environment variables configured locally

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd celesto_agent_flight_recorder
```

### 2. Configure environment variables

Copy the example configuration:

```bash
cp .env.example .env
```

Update `.env` locally with the values required by your implementation. Keep real credentials private and never commit `.env`.

Use placeholders in `.env.example`, not working API keys.

### 3. Start the application

```bash
docker compose up -d --build
```

Check container status:

```bash
docker compose ps
```

Inspect logs if a service is unhealthy:

```bash
docker compose logs --tail=100 api
docker compose logs --tail=100 ledger
```

### 4. Check application health

```bash
curl -i http://localhost:8080/health
```

A successful health check should return HTTP 200.

### 5. Open API documentation

With the service running, open:

http://localhost:8080/docs

The Swagger UI provides an interactive view of the endpoints defined by the application.

## API endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Check API health |
| `/api/runs` | GET | Retrieve recorded runs |
| `/api/runs` | POST | Register a run after request validation |
| `/api/agent/proof` | POST | Trigger the configured proof workflow, subject to the implementation and Celesto credentials |

Consult the running Swagger documentation for exact request schemas and response formats.

### Request validation

Run registration validates fields including the sandbox name, execution state, and execution target. The configured execution target must be `celesto_sandbox`.

For the submission requirements, invalid request payloads should return HTTP 400. Valid requests should return HTTP 201 when a new run is created successfully.

## How I used Celesto

Celesto integration is intended to provide a controlled environment for agent command execution. The executor attaches to a configured computer, checks commands against the application's safety rules, records the decision, and returns the execution result.

The configured computer identifier and API credentials must be supplied through environment variables. The executor's current lifecycle behavior should be distinguished from sandbox creation and deletion: attaching to an existing computer does not, by itself, demonstrate that the application created or cleaned up that computer.

Live execution results must be verified independently from local API and unit-test results.

## Eval report

The `reports/` directory organizes evidence for the project's evaluation requirements:

- `problem.json` — problem definition and proposed solution.
- `capabilities.json` — capability descriptions and supporting evidence.
- `lifecycle.json` — declared lifecycle and cleanup behavior.
- `reliability.json` — run measurements and aggregate statistics.
- `postmortem.md` — reliability analysis and lessons learned.
- `containment.json` — containment test outcome and evidence references.
- `failure_policy.json` — selected failure-handling policy.
- `failure_trace.jsonl` — structured failure-policy trace.
- `concurrency.json` — concurrency experiment records.

Reports should reflect actual observations. Do not treat sample data, static structural checks, or fabricated measurements as completed live evaluations.

## Containment test

The containment test is intended to demonstrate that a selected unsafe or suspicious action is blocked and that the host environment remains untouched.

The report should identify the attack scenario, whether the action was blocked, whether the host remained untouched, and the evidence files supporting those claims.

A report alone is not proof of containment. Validate the corresponding evidence and ensure that the test was performed safely in the intended environment.

## State and failure design

Run records use explicit execution states, including:

- `created`
- `ready`
- `running`
- `succeeded`
- `failed`
- `deleted`

The API validates state values before accepting run records. Failure-policy evidence should document the selected strategy—resume, rollback, or fresh execution—and explain the decision.

Lifecycle cleanup claims must match the actual executor implementation and observed results.

## Verification

Run the automated tests:

```bash
docker compose exec api python -m pytest -q
```

Run the structural report verifier:

```bash
docker compose exec api python scripts/verify.py
```

Check the API:

```bash
curl -i http://localhost:8080/health
curl -i http://localhost:8080/api/runs
```

Test invalid execution-target validation:

```bash
curl -i -X POST http://localhost:8080/api/runs \
  -H "Content-Type: application/json" \
  -d '{"run_id":"run-invalid-demo","sandbox_name":"sbx-invaliddemo01","problem_id":"validation-check","state":"created","execution_target":"host"}'
```

For the specified submission contract, this request should return HTTP 400.

Automated tests and structural verification do not independently establish that live Celesto execution, containment, concurrency, or all reliability measurements have passed. Verify those results using the corresponding evidence.

## Security considerations

- Keep `.env` and all real credentials out of version control.
- Commit `.env.example` with placeholders only.
- Validate commands before execution.
- Keep an auditable record of allowed and blocked commands.
- Execute untrusted commands only within an appropriately isolated environment.
- Do not claim that a host is untouched without supporting evidence.

## Limitations

Live Celesto operations depend on account permissions, available computers, API credentials, and service availability. Local container health and automated tests can pass even when a live cloud operation is unavailable or fails.

The scope of this project is defined by the implemented endpoints, executor behavior, and verified evidence. Any unsupported capabilities should be documented as limitations rather than presented as completed functionality.

## Conclusion

Celesto Agent Flight Recorder provides a structured foundation for tracking agent execution, validating run records, and collecting audit evidence through a containerized API and persistent ledger. Its effectiveness should be assessed using automated tests, report validation, and independently verified live execution results.
