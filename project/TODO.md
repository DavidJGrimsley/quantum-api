# Quantum API Master TODO and Roadmap

This file is the single source of truth for implementation planning.

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

## Phase 3.75 - Identerest Login + Key Lifecycle Rollout

Goal: finalize Identerest-authenticated key management from Portfolio through Quantum API.

- [x] Keep key-management endpoint contracts stable (`/v1/keys*`).
- [x] Keep auth split stable (bearer JWT for `/v1/keys*`, `X-API-Key` elsewhere).
- [x] Harden Supabase schema runbook with `pgcrypto` and explicit owner-scoped RLS policies.
- [x] Align README rollout steps to Identerest Supabase migration flow.
- [x] Add active key-cap safeguard per owner (`MAX_ACTIVE_API_KEYS_PER_USER`) with 409 responses on overflow.
- [x] Add total key-history cap safeguard per owner (`MAX_TOTAL_API_KEYS_PER_USER`, default `100`) to prevent unbounded rotate/revoke history growth.
- [x] Add revoked-key cleanup endpoints (`DELETE /v1/keys/{key_id}`, `DELETE /v1/keys/revoked`) to keep user key history manageable.
- [x] Ensure Supabase JWT verification supports current JWKS key types (including ES256/EC).
- [x] Execute production migration in Identerest Supabase and verify table/policy presence.
- [ ] Run full live flow validation: login -> create -> rotate -> revoke -> runtime rejection checks.
- [ ] Capture post-rollout verification notes in `project/questions.md` or release log.

## Phase 1 - Core Power API (High Priority)

Goal: unlock the most practical quantum capability quickly.

### Circuit Execution

- [x] Add `POST /v1/circuits/run` (locked path for Phase 1)
- [x] Support multi-qubit circuit definitions
- [x] Support `shots`-based sampling
- [x] Return measurement counts
- [x] Support optional statevector output for simulator backends
- [x] Add strict schema validation for circuit payloads

### Core Quality for Circuit Execution

- [x] Add deterministic tests for circuit runner behavior
- [x] Add validation/error-path tests (invalid gate, invalid qubit index, invalid shots)
- [x] Add resource limits for qubits, depth, shots, and execution time
- [x] Add benchmark tests for common circuits (non-CI-blocking)

### Completion Criteria

- [x] `/v1/circuits/run` can execute Bell, GHZ, and simple rotation circuits with stable results and clear errors

## Phase 2 - Compilation and Backend Discovery

Goal: make circuits portable and hardware-aware.

### Transpilation and Backend Metadata

- [x] Add `POST /v1/transpile`
- [x] Add `GET /v1/list_backends`
- [x] Return basis gates, coupling map summary, qubit count, simulator/hardware flags
- [x] Add backend filtering options (simulator only, min qubits, provider)

### QASM Interop

- [x] Add `POST /v1/qasm/import` (OpenQASM 2/3)
- [x] Add `POST /v1/qasm/export` (circuit to QASM)
- [x] Add validation and parser error normalization

### Completion Criteria

- [x] Users can submit QASM, transpile for a selected backend, and inspect backend capabilities before execution

## Phase 3 - Security and Production Hardening

Goal: make public operation safe and sustainable.

### Access Control and Abuse Protection

- [x] Add API key authentication for non-health endpoints
- [x] Add rate limiting per key/IP
- [x] Add request quota policies and consistent 429 responses
- [x] Add CORS allowlist configuration by environment

### Operational Hardening

- [x] Structured logging and request correlation IDs
- [x] Metrics and observability (latency, error rate, queue pressure)
- [x] SLO definitions and alerting rules
- [x] Deployment playbooks for staging and production

### Completion Criteria

- [x] Service can be safely exposed publicly with abuse controls and observability in place

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

### Portfolio Metadata Contract (`/public-facing/api/quantum/portfolio.json`)

- [ ] Final-phase cutover: ensure `/public-facing/api/quantum/portfolio.json` is re-added/served by the current deployment stack as a first-class public contract.
- [ ] Treat `portfolio.json` as a release artifact: update it whenever API endpoints, schemas, docs URLs, version, or health/docs links change.
- [ ] Add a release checklist item (or CI guard) that fails if `portfolio.json` is stale against current API behavior.

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
