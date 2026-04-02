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
- [x] Publish a concrete rollout gate/checklist for deployment and recovery.
- [x] Add executable rollback verification command (`scripts/verify_key_lifecycle.py`) and wire it into release docs/TODO.
- [x] Run full live flow validation: login -> create -> rotate -> revoke -> runtime rejection checks.
- [x] Capture post-rollout verification notes in release docs/TODO.

## Phase 3.8 - Portfolio endpoint migration

- [x] Add public metadata contract at `GET /v1/portfolio.json`.
- [x] Generate portfolio metadata dynamically from OpenAPI (endpoints, schemas, auth policy).
- [x] Keep `/v1/portfolio.json` public while preserving existing auth rules for protected endpoints.
- [x] Migrate portfolio/Expo API pages to `/v1` metadata and runtime endpoints only (no legacy route compatibility).
- [x] Ensure frontend protected demo calls use `EXPO_PUBLIC_QUANTUM_API_KEY` when present with graceful fallback UX.
- [ ] Add release/CI smoke check proving portfolio examples remain executable as API contracts evolve.

## Phase 3.9 - VPS Deploy and Redis setup

## Phase 4 - BYO IBM Runtime and Hardware Jobs (V1)

Goal: expand beyond local simulation without taking on managed-provider billing in the first release.

### BYO IBM Credentials and Provider Resolution

- [x] Add bearer-authenticated IBM credential profile endpoints (`/v1/ibm/profiles*`)
- [x] Store encrypted IBM tokens plus masked display metadata in Supabase-backed persistence
- [x] Support multiple named IBM profiles per user with a default profile contract
- [x] Refactor IBM backend discovery/transpile to resolve the owner's saved IBM profile
- [x] Keep server-global IBM env vars as local/self-host fallback instead of the primary hosted path

### Async IBM Hardware Jobs

- [x] Add API-key-authenticated hardware job submit/status/result/cancel endpoints
- [x] Persist local execution jobs with normalized status contracts and remote job ids
- [x] Use poll-on-read job refresh for V1 instead of introducing a worker queue
- [x] Keep `/v1/circuits/run` simulator-first and synchronous

### Phase 4 V1 Rollout Workstream

- [x] Extend `/v1/portfolio.json` so the new IBM/profile/job routes appear with the correct auth mode
- [x] Add backend/API tests for IBM profile CRUD, scoping, masking, and hardware job lifecycle
- [ ] Run the updated Supabase schema migration in the live Identerest project
- [ ] Add live smoke validation for the full BYO flow:
  - [ ] sign in
  - [ ] save IBM profile
  - [ ] create Quantum API key
  - [ ] list IBM backends
  - [ ] submit hardware job
  - [ ] poll status
  - [ ] fetch result or provider error

### External Portfolio and Identerest UI Workstream

- [ ] Modify the Identerest schema migration flow to include `ibm_credential_profiles` and `quantum_execution_jobs`
- [ ] Update the portfolio API key management component with a collapsible `IBM Credentials` section
- [ ] Include add/edit/delete/default-selection and verify actions in that IBM credentials panel
- [ ] Add info copy explaining simulator-only usage vs BYO IBM hardware usage through the same API

### Future Optional Managed IBM Access

- [ ] Managed IBM access requires billing, quotas, abuse controls, cost caps, failed-job handling, and legal/terms review before resale

### Later Runtime Expansion

- [ ] Add `Estimator`-oriented contracts once hardware job primitives are stable
- [ ] Add provider abstraction beyond IBM where it meaningfully improves product scope
- [ ] Evaluate dynamic circuits support
- [ ] Add optional noise model controls for simulator runs
- [ ] Add basic error-mitigation controls where practical

### Completion Criteria

- [ ] Users can save BYO IBM credentials, discover IBM backends, transpile against them, and run hardware-backed jobs through stable contracts

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

## Phase 6 - Client and Engine Integrations & Migrations (from old quantum-api)

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

### Migrations
- [x] Expo animation
- [x] Portfolio website (endpoint that drives the info page)
- [ ] Godot Game

## Phase 7 - Release Governance and Long-Term Maintenance

Goal: keep the platform stable as capabilities grow.

### Portfolio Metadata Contract (`/v1/portfolio.json`)

- [x] Final-phase cutover: ensure `/v1/portfolio.json` is served by the current deployment stack as a first-class public contract.
- [x] Treat `portfolio.json` as a release artifact: generate it dynamically from current OpenAPI metadata, docs URL, health URL, and version.
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
