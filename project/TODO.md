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
- [x] Add explicit release/CI smoke check proving portfolio examples remain executable as API contracts evolve.

## Phase 3.9 - VPS Deploy and Redis setup

- [x] Document VPS Redis/env setup runbook (`project/VPS-redis-plan.md`).
- [x] Keep staging/production deployment playbooks current (`docs/operations/deploy-staging.md`, `docs/operations/deploy-production.md`).
- [x] Keep deployed Nginx routing reference for `/public-facing/api/quantum/*` paths (`project/nginx-quantum-api-location.conf`).

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
- [x] Add backend/API test coverage proving IBM transpile resolves a stored IBM profile
- [x] Run the updated Supabase schema migration in the live Identerest project
- [x] Run live BYO IBM verification against the target environment and capture the result in release notes/TODO:
  - [x] sign in
  - [x] save IBM profile
  - [x] create Quantum API key
  - [x] list IBM backends
  - [x] transpile against an IBM backend
  - [x] submit hardware job
  - [x] poll status
  - [x] fetch result or provider error
  - [x] record date, environment, backend, terminal status, artifact, and cleanup outcome
  - Live verification note (2026-04-02, production):
    base URL `https://davidjgrimsley.com/public-facing/api/quantum/v1`
    profile `Portfolio` verified in the live UI
    backend `ibm_kingston`
    local job `28ee0f04-3b7d-4993-9cd4-2d4f72c2d92e`
    remote job `d778ifohnndc73865a7g`
    terminal status `succeeded`
    completed at `2026-04-02T17:10:06.328223Z`
    result counts `{"0": 490, "1": 22}` for `shots=512`
    note: `scripts/verify_byo_ibm_flow.py` is available for repeatable future reruns of the same rollout check

### External Portfolio and Identerest UI Workstream

- [x] Modify the Identerest schema migration flow to include `ibm_credential_profiles` and `quantum_execution_jobs`
- [x] Update the portfolio API key management component with a collapsible `IBM Credentials` section
- [x] Include add/edit/delete/default-selection and verify actions in that IBM credentials panel
- [x] Add info copy explaining simulator-only usage vs BYO IBM hardware usage through the same API

### Completion Criteria

- [x] Users can save BYO IBM credentials, discover IBM backends, transpile against them, and run hardware-backed jobs through stable contracts (confirmed by a recorded live verifier run)

## Phase 5 - Qiskit Ecosystem Expansion (Advanced)

Goal: cover major Qiskit domain capabilities through focused APIs.

### Phase 5.1 - Structural Refactor

- [x] Replace the single advanced-domain router with domain routers (`algorithms`, `optimization`, `experiments`, `finance`, `machine_learning`, `nature`)
- [x] Split advanced-domain models into domain modules plus shared Qiskit-facing schemas
- [x] Replace `services/phase5_*` and `services/phase5_common.py` with domain packages plus `services/qiskit_common/*`
- [x] Rename stage-prefixed tests and notebook/docs asset paths so `phase5` does not leak into runtime code
- [x] Preserve existing public `/v1` paths, auth rules, examples, and portfolio/OpenAPI behavior during the refactor

### Phase 5.2 - Algorithms Namespace

- [x] Add `POST /v1/algorithms/grover_search`
- [x] Add `POST /v1/algorithms/amplitude_estimation`
- [x] Add `POST /v1/algorithms/phase_estimation`
- [x] Add `POST /v1/algorithms/time_evolution`
- [x] Add docs, notebooks, API tests, and perf coverage for the new `/v1/algorithms/*` routes

### Phase 5.3 - Optimization Expansion

- [x] Keep `POST /v1/optimization/qaoa`
- [x] Keep `POST /v1/optimization/vqe`
- [x] Add `POST /v1/optimization/maxcut`
- [x] Add `POST /v1/optimization/knapsack`
- [x] Add `POST /v1/optimization/tsp`
- [x] Add docs, notebooks, API tests, and perf coverage for the optimization application routes

### Phase 5.4 - Finance Expansion

- [x] Keep `POST /v1/finance/portfolio_optimization`
- [x] Add `POST /v1/finance/portfolio_diversification`
- [x] Keep finance payloads caller-supplied only (no live market-data provider integration)
- [x] Add docs, notebooks, and API/perf coverage for the finance routes

### Phase 5.5 - Machine Learning Expansion

- [x] Keep `POST /v1/ml/kernel_classifier`
- [x] Add `POST /v1/ml/vqc_classifier`
- [x] Add `POST /v1/ml/qsvr_regressor`
- [x] Keep ML workflows request-scoped only (no persisted models or async training jobs)
- [x] Add docs, notebooks, and API coverage for the ML routes

### Phase 5.6 - Nature Expansion

- [x] Keep `POST /v1/nature/ground_state_energy`
- [x] Add `POST /v1/nature/fermionic_mapping_preview`
- [ ] Add `POST /v1/nature/excited_state_energy`
  Note: deferred for now because `qiskit-nature 0.7.2` excited-state imports still fail against `qiskit 2.3.x` in the current environment (`BaseEstimator` vs V2 primitives). Track upstream compatibility or a maintained fork/PR before exposing this route.
- [x] Add docs, notebooks, and API coverage for the currently supported Nature routes

### Phase 5.7 - Experiments Expansion

- [x] Keep `POST /v1/experiments/state_tomography`
- [x] Keep `POST /v1/experiments/randomized_benchmarking`
- [x] Add `POST /v1/experiments/quantum_volume`
- [x] Add `POST /v1/experiments/t1`
- [x] Add `POST /v1/experiments/t2ramsey`
- [x] Add docs, notebooks, API tests, and perf coverage for the experiment routes

### Product and Contract Design

- [x] Define per-domain contracts with clear input constraints
- [x] Add examples and notebook-style reference docs
- [x] Add dedicated test suites per domain module

### Completion Criteria

- [x] Each adopted domain has at least one production-quality endpoint with tests and docs
- [x] Add algorithm-first endpoints alongside the domain modules without changing the existing `/v1` contract style
- [x] Keep mixed optional-dependency behavior with normalized `503 provider_unavailable` responses
- [ ] Close the final Nature excited-state gap once upstream Qiskit Nature compatibility lands or we contribute a maintained fix

## Phase 6 - Client and Engine Integrations & Migrations (from old quantum-api) - SDK

Goal: make adoption easy across game and app stacks.

### JS SDK

- [x] Promote `sdk/js` scaffold to package-ready ESM package
- [x] Expand `sdk/js` coverage to the full current `/v1` surface
- [x] Add SDK auth support for both `X-API-Key` and bearer-token flows with per-request override
- [x] Add structured SDK error handling (`error`, `message`, `details`, `request_id`, status, headers)
- [x] Normalize SDK base URL handling for both local `/v1` and mounted `/public-facing/api/quantum/v1`

### Python SDK

- [x] Promote `sdk/python` scaffold to package-ready wheel
- [x] Expand `sdk/python` coverage to the full current `/v1` surface
- [x] Add Python SDK context-manager ergonomics and stronger typing metadata
- [x] Add semantic versioning and changelog policies
- [x] Add SDK bootstrap/setup docs so `uv`, `tsc`, and related tooling are explicit instead of assumed
- [x] Add Python SDK methods for `POST /v1/qasm/run` and `POST /v1/jobs/qasm`
- [x] Add typed request/response entries for QASM run and QASM job submission
- [x] Install local test tooling (`uv`, `pytest`) in the dev environment
- [x] Run focused Python SDK and QASM contract tests after PennyLane groundwork changes
- [x] Build `sdk/python` artifacts (`sdist` + `wheel`) and validate install from a clean venv
- [ ] Publish `sdk/python` package to PyPI
- [x] Add/verify Python package publish workflow using PyPI Trusted Publisher (OIDC) in CI

### Godot

- [x] Build reusable Godot addon client (`addons/quantum_api_client/`)
- [x] Support both backend-proxy mode and optional direct API-key mode in the Godot client
- [x] Migrate legacy Godot runtime calls to mounted `/v1` endpoints
- [x] Add install docs and sample scene integration

### Unreal

- [x] Build runtime HTTP wrapper (C++ + Blueprint callable layer)
- [x] Scope the first Unreal plugin to `health`, `text/transform`, and `gates/run` before optional `circuits/run` and `jobs/*`
- [x] Default Unreal docs to backend-proxy mode and keep direct API-key mode as dev/demo only
- [x] Keep Python usage restricted to editor tooling
- [x] Add a future public Unreal release milestone so setup stays easy for external game developers

### Unity

- [x] Build runtime C# client wrapper (`UnityWebRequest`)
- [x] Add coroutine/async usage examples and fallback modes

### Pennylane

- [x] Add additive API groundwork endpoint `POST /v1/qasm/run` (finite-shot + analytic statevector mode)
- [x] Add additive IBM async endpoint `POST /v1/jobs/qasm`
- [x] Add Python SDK support for QASM run and QASM job submission
- [x] Add backend/API/SDK test coverage for the new QASM run + QASM job flow
- [x] Create `sdk/pennylane/` package scaffold with `pyproject.toml` and plugin entry points
- [x] Implement PennyLane device plugin (`QuantumApiDevice`) using QASM serialization and API execution
- [x] Implement finite-shot measurement reconstruction + analytic statevector handling in the plugin
- [x] Add plugin tests (unit + mocked transport + optional integration smoke)
- [x] Build and validate `sdk/pennylane` artifacts from a clean venv
- [ ] Publish PennyLane package(s) to PyPI
- [x] Add/verify CI publish workflow using PyPI Trusted Publisher (OIDC) for PennyLane package release


### Completion Criteria

- [ ] All five client paths (JS, Python, Godot, Unreal, Unity) have maintained reference integrations
- [ ] Godot migration acts as the first validated reference integration for the reusable addon/client path
- [x] JS/Python SDKs are package-ready even if public publishing remains deferred
- [ ] JS SDK tested
- [x] Python SDK tested
- [ ] Unreal Engine local plugin tested
- [ ] Godot local plugin tested
- [ ] Unity local plugin tested

### Migrations
- [x] Expo animation
- [x] Portfolio website (endpoint that drives the info page and animation)
- [x] Godot Game - Echoes of Light
- [ ] Unreal Engine game - Entanglement
- [ ] Create Unity Game
- [ ] Create Roblox, Minecraft, Fortnite game
 
## Phase 7 - Release Governance and Long-Term Maintenance

Goal: keep the platform stable as capabilities grow.

### Portfolio Metadata Contract (`/v1/portfolio.json`)

- [x] Final-phase cutover: ensure `/v1/portfolio.json` is served by the current deployment stack as a first-class public contract.
- [x] Treat `portfolio.json` as a release artifact: generate it dynamically from current OpenAPI metadata, docs URL, health URL, and version.
- [x] Add an explicit CI portfolio smoke step that fails if `portfolio.json` examples drift from current API behavior.

### Release Discipline

- [x] Enforce semantic versioning rules across API and SDKs
- [ ] Add deprecation policy and sunset timelines
- [x] Add compatibility matrix (API versions vs SDK versions)
- [x] Split "package-ready" from "public publishing" in release checklists so external publication remains an explicit follow-up decision

### Future Distribution Follow-On

- [ ] Publish JS SDK package after Phase 6 validation gates are green
- [ ] Publish Python SDK package after Phase 6 validation gates are green
- [ ] Publish PennyLane package(s) after Phase 6 PennyLane validation gates are green
- [ ] Package and publish Unreal runtime plugin after Godot reference migration is stable

### Quality and Reliability

- [ ] Expand integration and load tests
- [ ] Add periodic dependency/security audits
- [ ] Add cost and performance review cadence

### Extra Features - Quantum Echo and Gameplay APIs

- [x] Quantum Gate API - RY rotation gates for true randomness
- [x] Quantum Text Transformation - Unicode effects powered by quantum randomness
- [x] Portfolio Integration - live quantum animation in Quantum Echo project
- [x] Multi-qubit circuits for more complex quantum states
- [ ] Quantum entanglement demonstration API
- [x] Grover's algorithm for quantum search
- [ ] Quantum random number generator (QRNG) endpoint
- [ ] Quantum game mechanics for procedural generation
- [ ] Quantum circuit visualization in the API response
- [x] Real quantum hardware access via IBM Quantum cloud (BYO credentials)

## Deferred Backlog (Post-Phase-5 and Non-Blocking)

### Managed IBM Access (Deferred)

- [ ] Managed IBM access requires billing, quotas, abuse controls, cost caps, failed-job handling, and legal/terms review before resale

### Runtime Expansion (Deferred from Phase 4)

- [ ] Add `Estimator`-oriented contracts once hardware job primitives are stable
- [ ] Add provider abstraction beyond IBM where it meaningfully improves product scope
- [ ] Evaluate dynamic circuits support
- [ ] Add optional noise model controls for simulator runs
- [ ] Add basic error-mitigation controls where practical

### Upstream Ecosystem Contributions (Deferred)

- [ ] Investigate and, if appropriate, contribute a `qiskit-nature` Qiskit-2 compatibility fix for excited-state solvers (`QEOM` / `ExcitedStatesEigensolver`) so `/v1/nature/excited_state_energy` can be added cleanly later

## Notes on Scope

- This roadmap targets broad Qiskit coverage over multiple phases.
- "Complete" means practical platform completeness, not a one-to-one mirror of every internal Qiskit API symbol.
- Endpoint names in future phases should be finalized once schemas are locked, but the capability goals in this file are the source of truth.
