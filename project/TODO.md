# Quantum API Master TODO and Roadmap

This file is the single source of truth for implementation planning.

The previous planning files are now condensed into this roadmap:
- `project/quantum-api-plan.md`
- `project/quantum-api-research-plan.md`

## North Star

Build a production-ready Quantum API that starts with high-power core endpoints and expands toward broad Qiskit ecosystem coverage over time.

## Current Status (Already Delivered)

### Foundation and Backend Baseline

- [x] FastAPI + Uvicorn project scaffold with modular structure (`api`, `models`, `services`)
- [x] Core endpoint set:
  - [x] `GET /v1/health`
  - [x] `GET /v1/echo-types`
  - [x] `POST /v1/gates/run`
  - [x] `POST /v1/text/transform`
- [x] Runtime guardrails:
  - [x] request validation
  - [x] max text length
  - [x] request timeout middleware
  - [x] sanitized error responses
- [x] DevOps baseline:
  - [x] Dockerfile
  - [x] GitHub Actions CI
  - [x] Ruff + Pytest
  - [x] Apache-2.0 license
- [x] SDK scaffolds:
  - [x] `sdk/js`
  - [x] `sdk/python`
- [x] Client migration docs:
  - [x] Godot
  - [x] Expo
  - [x] Unreal
  - [x] Unity

## Phase 1 - Core Power API (High Priority)

Goal: unlock the most practical quantum capability quickly.

### Circuit Execution

- [ ] Add `POST /v1/run_circuit` (or `POST /v1/circuits/run`, choose one and lock it)
- [ ] Support multi-qubit circuit definitions
- [ ] Support `shots`-based sampling
- [ ] Return measurement counts
- [ ] Support optional statevector output for simulator backends
- [ ] Add strict schema validation for circuit payloads

### Core Quality for Circuit Execution

- [ ] Add deterministic tests for circuit runner behavior
- [ ] Add validation/error-path tests (invalid gate, invalid qubit index, invalid shots)
- [ ] Add resource limits for qubits, depth, and execution time
- [ ] Add benchmark tests for common circuits

### Completion Criteria

- [ ] `/run_circuit` can execute Bell, GHZ, and simple rotation circuits with stable results and clear errors

## Phase 2 - Compilation and Backend Discovery

Goal: make circuits portable and hardware-aware.

### Transpilation and Backend Metadata

- [ ] Add `POST /v1/transpile`
- [ ] Add `GET /v1/list_backends`
- [ ] Return basis gates, coupling map summary, qubit count, simulator/hardware flags
- [ ] Add backend filtering options (simulator only, min qubits, provider)

### QASM Interop

- [ ] Add `POST /v1/qasm/import` (OpenQASM 2/3)
- [ ] Add `POST /v1/qasm/export` (circuit to QASM)
- [ ] Add validation and parser error normalization

### Completion Criteria

- [ ] Users can submit QASM, transpile for a selected backend, and inspect backend capabilities before execution

## Phase 3 - Security and Production Hardening

Goal: make public operation safe and sustainable.

### Access Control and Abuse Protection

- [ ] Add API key authentication for non-health endpoints
- [ ] Add rate limiting per key/IP
- [ ] Add request quota policies and consistent 429 responses
- [ ] Add CORS allowlist configuration by environment

### Operational Hardening

- [ ] Structured logging and request correlation IDs
- [ ] Metrics and observability (latency, error rate, queue pressure)
- [ ] SLO definitions and alerting rules
- [ ] Deployment playbooks for staging and production

### Completion Criteria

- [ ] Service can be safely exposed publicly with abuse controls and observability in place

## Phase 4 - Runtime and Hardware Integrations

Goal: expand beyond local simulation.

### Qiskit Runtime and Providers

- [ ] Add IBM Runtime integration path (Sampler/Estimator)
- [ ] Add provider abstraction for pluggable backends
- [ ] Add hardware job submission and job-status endpoints
- [ ] Add asynchronous job model for long-running workloads

### Advanced Execution Features

- [ ] Evaluate dynamic circuits support
- [ ] Add optional noise model controls for simulator runs
- [ ] Add basic error-mitigation controls where practical

### Completion Criteria

- [ ] Users can run both simulator and hardware-backed jobs through stable contracts

## Phase 5 - Qiskit Ecosystem Expansion (Advanced)

Goal: cover major Qiskit domain capabilities through focused APIs.

### Algorithms and Domain Modules

- [ ] Optimization endpoints (QAOA/VQE workflows)
- [ ] Finance endpoints (portfolio/estimation workflows)
- [ ] Machine Learning endpoints (kernel/classifier primitives)
- [ ] Nature endpoints (selected chemistry/physics workflows)
- [ ] Experiments endpoints (selected benchmarking/tomography flows)

### Product and Contract Design

- [ ] Define per-domain contracts with clear input constraints
- [ ] Add examples and notebook-style reference docs
- [ ] Add dedicated test suites per domain module

### Completion Criteria

- [ ] Each adopted domain has at least one production-quality endpoint with tests and docs

## Phase 6 - Client and Engine Integrations

Goal: make adoption easy across game and app stacks.

### SDK Productization

- [ ] Promote `sdk/js` scaffold to publishable package
- [ ] Promote `sdk/python` scaffold to publishable package
- [ ] Add semantic versioning and changelog policies

### Godot

- [ ] Build reusable Godot addon client (`addons/quantum_api_client/`)
- [ ] Add install docs and sample scene integration

### Unreal

- [ ] Build runtime HTTP wrapper (C++ + Blueprint callable layer)
- [ ] Keep Python usage restricted to editor tooling

### Unity

- [ ] Build runtime C# client wrapper (`UnityWebRequest`)
- [ ] Add coroutine/async usage examples and fallback modes

### Completion Criteria

- [ ] All four client paths (JS, Python, Godot, Unreal, Unity) have maintained reference integrations

## Phase 7 - Release Governance and Long-Term Maintenance

Goal: keep the platform stable as capabilities grow.

### Release Discipline

- [ ] Enforce semantic versioning rules across API and SDKs
- [ ] Add deprecation policy and sunset timelines
- [ ] Add compatibility matrix (API versions vs SDK versions)

### Quality and Reliability

- [ ] Expand integration and load tests
- [ ] Add periodic dependency/security audits
- [ ] Add cost and performance review cadence

## Notes on Scope

- This roadmap targets broad Qiskit coverage over multiple phases.
- "Complete" means practical platform completeness, not a one-to-one mirror of every internal Qiskit API symbol.
- Endpoint names in future phases should be finalized once schemas are locked, but the capability goals in this file are the source of truth.
