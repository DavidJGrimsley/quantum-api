# Quantum API

Quantum API is a greenfield FastAPI service for quantum-inspired runtime features:

- `/v1/health`
- `/v1/portfolio.json`
- `/v1/echo-types`
- `/v1/gates/run`
- `/v1/circuits/run`
- `/v1/list_backends`
- `/v1/transpile`
- `/v1/qasm/import`
- `/v1/qasm/export`
- `/v1/text/transform`
- `/v1/keys`
- `/v1/ibm/profiles`
- `/v1/ibm/profiles/{profile_id}`
- `/v1/ibm/profiles/{profile_id}/verify`
- `/v1/jobs/circuits`
- `/v1/jobs/{job_id}`
- `/v1/jobs/{job_id}/result`
- `/v1/jobs/{job_id}/cancel`
- `/v1/keys/{key_id}` (delete revoked key)
- `/v1/keys/revoked` (bulk delete revoked keys)
- `/v1/keys/{key_id}/revoke`
- `/v1/keys/{key_id}/rotate`
- `/v1/optimization/qaoa`
- `/v1/optimization/vqe`
- `/v1/experiments/state_tomography`
- `/v1/experiments/randomized_benchmarking`
- `/v1/finance/portfolio_optimization`
- `/v1/ml/kernel_classifier`
- `/v1/nature/ground_state_energy`
- `/metrics` (internal metrics endpoint)

This repository is intentionally not backward compatible with the previous `public-facing/api/quantum/*` paths.

## Tech Stack

- Python 3.11+
- FastAPI + Uvicorn
- Pydantic v2
- Redis (rate limiting and quotas)
- Prometheus client metrics
- Optional qiskit/qiskit-aer runtime (with classical fallback mode)
- Optional qiskit-ibm-runtime integration for BYO IBM backend discovery and hardware jobs
- Ruff + Pytest
- Docker
- GitHub Actions CI

## Quickstart (uv)

```bash
uv sync --extra dev
uv run uvicorn quantum_api.main:app --reload
```

Open docs at `http://127.0.0.1:8000/docs`.

For local development, use API key `qapi_devlocal_0123456789abcdef0123456789abcdef` with the default `.env.example` values.

Optional Phase 5 extras:

```bash
uv sync --extra phase5-optimization --extra phase5-experiments --extra phase5-finance --extra phase5-ml --extra phase5-nature --extra phase5-docs
```

## API Contract

### Authentication and Rate Limits

- `GET /v1/health` and `GET /v1/portfolio.json` are public.
- `GET /v1/keys`, `POST /v1/keys`, `DELETE /v1/keys/{key_id}`, `DELETE /v1/keys/revoked`, `POST /v1/keys/{key_id}/revoke`, `POST /v1/keys/{key_id}/rotate`, and all `/v1/ibm/profiles*` endpoints require `Authorization: Bearer <supabase_jwt>`.
- All other protected `/v1/*` endpoints require `X-API-Key` (DB-managed key records only; no `API_KEYS_JSON` fallback).
- Successful protected responses include:
  - `X-Request-ID`
  - `RateLimit-Limit`
  - `RateLimit-Remaining`
  - `RateLimit-Reset`
- `429` responses include `Retry-After` and a normalized envelope.
- Error envelope shape is standardized as:

```json
{
  "error": "too_many_requests",
  "message": "Rate limit or quota exceeded.",
  "details": {
    "policy": "key_minute",
    "retry_after_seconds": 15
  },
  "request_id": "2e65df20-7f95-4709-bec0-69a2e4e58abf"
}
```

### `GET /v1/health`
Response fields:

- `status`
- `service`
- `version`
- `qiskit_available`
- `runtime_mode`

### `GET /v1/portfolio.json`
- Public metadata contract used by portfolio pages and app integrations.
- Built dynamically from the current OpenAPI surface with endpoint auth classification:
  - `public`
  - `api_key`
  - `bearer_jwt`
- When the API is mounted behind a prefix such as `/public-facing/api/quantum`, each endpoint `path` in `portfolio.json` is emitted as a request-ready mounted path.
- `operationPath` keeps the canonical FastAPI/OpenAPI route such as `/v1/optimization/qaoa`.

For a plain-English live VPS testing walkthrough, see [docs/operations/phase5-beginner-testing.md](docs/operations/phase5-beginner-testing.md).

### `GET /v1/echo-types`
Lists canonical transformation categories and descriptions from one enum source.

### Key Management Endpoints (`/v1/keys*`)

- `GET /v1/keys`: list current user's keys (masked metadata only).
- `POST /v1/keys`: create a key and return the raw key exactly once.
- `DELETE /v1/keys/{key_id}`: permanently delete one revoked key from history.
- `DELETE /v1/keys/revoked`: permanently delete all revoked keys for the current user.
- `POST /v1/keys/{key_id}/revoke`: revoke an existing key.
- `POST /v1/keys/{key_id}/rotate`: atomically rotate key (old key becomes invalid, new raw key shown once).

All key-management endpoints are user-scoped to the JWT subject (`sub`) and require a valid Supabase bearer token.

### IBM Profile Endpoints (`/v1/ibm/profiles*`)

- `GET /v1/ibm/profiles`: list the current user's saved IBM credential profiles.
- `POST /v1/ibm/profiles`: save a new named IBM credential profile.
- `PATCH /v1/ibm/profiles/{profile_id}`: rename a profile, replace token/instance/channel, or switch the default profile.
- `DELETE /v1/ibm/profiles/{profile_id}`: remove one saved profile.
- `POST /v1/ibm/profiles/{profile_id}/verify`: attempt a live IBM Runtime lookup and persist `verified` or `invalid`.

IBM profile rules:

- Profiles are user-scoped to the bearer JWT subject.
- `profile_name` must be unique per user.
- Raw IBM tokens are write-only. Responses return masked token metadata only.
- Stored-profile support requires `IBM_CREDENTIAL_ENCRYPTION_KEY` on the server.
- `IBM_CHANNEL` defaults to `ibm_quantum_platform`.
- Server-level `IBM_TOKEN` and `IBM_INSTANCE` remain available as a local/self-host fallback when no stored BYO profile is available.

Create request example:

```json
{
  "profile_name": "my-open-plan",
  "token": "ibm_api_token_here",
  "instance": "crn:v1:bluemix:public:quantum-computing:us-east:...",
  "channel": "ibm_quantum_platform",
  "is_default": true
}
```

### `POST /v1/gates/run`
Request:

```json
{
  "gate_type": "rotation",
  "rotation_angle_rad": 1.57079632679
}
```

Rules:

- `gate_type` must be one of `bit_flip`, `phase_flip`, `rotation`
- `rotation_angle_rad` is required only when `gate_type` is `rotation`

Response:

```json
{
  "gate_type": "rotation",
  "measurement": 1,
  "superposition_strength": 1.0,
  "success": false
}
```

### `POST /v1/circuits/run`
Request (Bell circuit example):

```json
{
  "num_qubits": 2,
  "operations": [
    { "gate": "h", "target": 0 },
    { "gate": "cx", "control": 0, "target": 1 }
  ],
  "shots": 1024,
  "include_statevector": false,
  "seed": 7
}
```

Operation rules:

- `gate` must be one of `x`, `z`, `h`, `ry`, `cx`
- `target` is required for every operation
- `theta` is required only for `ry`
- `control` is required only for `cx`
- `control` and `target` must be different for `cx`
- qubit indexes must be in range `[0, num_qubits - 1]`

Response:

```json
{
  "num_qubits": 2,
  "shots": 1024,
  "counts": {
    "00": 496,
    "11": 528
  },
  "backend_mode": "qiskit",
  "statevector": null
}
```

Notes:

- `counts` keys are zero-padded bitstrings from qiskit simulator output.
- Use `include_statevector: true` to include serialized amplitudes (`real`, `imag`) for each basis state.
- This endpoint is qiskit-dependent and returns `503` if qiskit is unavailable.

### `GET /v1/list_backends`
Query filters:

- `provider`: `aer` or `ibm`
- `simulator_only`: `true/false`
- `min_qubits`: integer `>= 1`
- `ibm_profile`: optional IBM profile name when `provider=ibm` (defaults to the owner's default saved profile)

Response fields:

- `backends`: list of backend summaries (`name`, `provider`, `is_simulator`, `is_hardware`, `num_qubits`, `basis_gates`, `coupling_map_summary`)
- `total`
- `filters_applied`
- `warnings` (optional, e.g. IBM provider unavailable when not explicitly requested)

Aer notes:

- The API lists modern `aer_simulator*` backends.
- Legacy aliases (`qasm_simulator`, `statevector_simulator`, `unitary_simulator`) are intentionally not exposed.

If `provider=ibm` and the request owner has no usable IBM profile or fallback credentials, the API returns:

```json
{
  "error": "provider_credentials_missing",
  "message": "IBM provider credentials are not configured for this user."
}
```

### `POST /v1/transpile`
Request accepts exactly one input source:

- `circuit` (JSON operation format), or
- `qasm` (`source`, `qasm_version` = `auto|2|3`)

Plus:

- `backend_name` (required)
- `provider` (`aer|ibm`, optional)
- `ibm_profile` (optional IBM profile name when `provider=ibm`; defaults to the owner's default saved profile)
- `optimization_level` (`0-3`)
- `seed_transpiler` (optional)
- `output_qasm_version` (`2|3`, default `3`)

Response fields:

- `backend_name`
- `provider`
- `input_format` (`circuit|qasm`)
- `num_qubits`, `depth`, `size`
- `operations` (normalized generic operations)
- `qasm_version`
- `qasm`

Validation note:

- Sending both `circuit` and `qasm` in one request returns `422`.

### `POST /v1/jobs/circuits`
Submit an asynchronous hardware execution job. Phase 4 V1 supports `provider: "ibm"` only.

Request:

```json
{
  "provider": "ibm",
  "backend_name": "ibm_kingston",
  "shots": 1024,
  "ibm_profile": "my-open-plan",
  "circuit": {
    "num_qubits": 2,
    "operations": [
      { "gate": "h", "target": 0 },
      { "gate": "cx", "control": 0, "target": 1 }
    ]
  }
}
```

Response fields:

- `job_id`
- `provider`
- `backend_name`
- `ibm_profile`
- `status`
- `remote_job_id`
- `created_at`
- `updated_at`

Notes:

- Jobs are scoped by the owning API key's `owner_user_id`, not by bearer JWT.
- Submit persists a local job row immediately, then status/result endpoints poll IBM on read and cache terminal state.

### `GET /v1/jobs/{job_id}`
Returns the normalized job contract with local status values:

- `queued`
- `running`
- `succeeded`
- `failed`
- `cancelling`
- `cancelled`

### `GET /v1/jobs/{job_id}/result`
Returns the cached terminal result for successful jobs. If the job is not finished yet, the API returns:

```json
{
  "error": "result_not_ready",
  "message": "Job 'job-id' has not produced a result yet.",
  "details": {
    "job_id": "job-id",
    "status": "running"
  }
}
```

### `POST /v1/jobs/{job_id}/cancel`
Attempts to cancel the remote hardware job and returns the updated normalized local status contract.

### `POST /v1/qasm/import`
Request:

```json
{
  "qasm": "OPENQASM 2.0; include \"qelib1.inc\"; qreg q[1]; h q[0];",
  "qasm_version": "auto"
}
```

Response fields:

- `detected_qasm_version` (`2|3`)
- `num_qubits`, `depth`, `size`
- `operations` (normalized generic operations)

### `POST /v1/qasm/export`
Request:

```json
{
  "circuit": {
    "num_qubits": 2,
    "operations": [
      { "gate": "h", "target": 0 },
      { "gate": "cx", "control": 0, "target": 1 }
    ]
  },
  "qasm_version": "3"
}
```

Response fields:

- `qasm_version`
- `qasm`
- `num_qubits`, `depth`, `size`

Default export version:

- QASM export defaults to OpenQASM 3.

### `POST /v1/text/transform`
Request:

```json
{
  "text": "memory signal and quantum circuit"
}
```

Response:

```json
{
  "original": "memory signal and quantum circuit",
  "transformed": "...",
  "coverage_percent": 80.0,
  "quantum_words": 4,
  "total_words": 5,
  "category_counts": {
    "scramble": 0,
    "reverse": 0,
    "ghost": 0,
    "quantum_caps": 0,
    "quantum_gates": 2,
    "quantum_entanglement": 0,
    "quantum_interference": 2,
    "original": 1
  }
}
```

### `GET /metrics` (Internal)

- Exposes Prometheus metrics.
- In `staging` and `production`, requires `X-Metrics-Token`.

## Runtime Modes

- `qiskit`: qiskit imports are available.
- `classical-fallback`: qiskit imports are unavailable; math-backed simulation is used.

Set `REQUIRE_QISKIT=true` to force 503 responses for runtime endpoints when qiskit is unavailable.
`/v1/circuits/run` always requires qiskit and returns `503` when qiskit is unavailable.

QASM 3 import notes:

- OpenQASM 3 import is best-effort.
- If `qiskit_qasm3_import` is missing, the API returns `qasm3_dependency_missing`.

## Configuration

Copy `.env.example` to `.env` and adjust values as needed.

- `APP_ENV`
- `API_PREFIX`
- `MAX_TEXT_LENGTH`
- `MAX_CIRCUIT_QUBITS`
- `MAX_CIRCUIT_DEPTH`
- `MAX_CIRCUIT_SHOTS`
- `ALLOW_ORIGINS`
- `DEV_CORS_ALLOW_LOCALHOST`
- `DEV_CORS_LOCAL_ORIGINS`
- `REQUEST_TIMEOUT_SECONDS`
- `REQUIRE_QISKIT`
- `IBM_TOKEN` (optional local/self-host fallback)
- `IBM_INSTANCE` (optional local/self-host fallback)
- `IBM_CHANNEL` (optional, default `ibm_quantum_platform`)
- `IBM_CREDENTIAL_ENCRYPTION_KEY` (required for stored BYO IBM profiles)
- `AUTH_ENABLED`
- `API_KEY_HEADER`
- `API_KEY_HASH_SECRET`
- `API_KEY_FORMAT_PREFIX`
- `API_KEY_PREFIX_LENGTH`
- `API_KEY_SECRET_LENGTH`
- `API_KEY_CACHE_TTL_SECONDS`
- `DEFAULT_KEY_RATE_LIMIT_PER_SECOND`
- `DEFAULT_KEY_RATE_LIMIT_PER_MINUTE`
- `DEFAULT_KEY_DAILY_QUOTA`
- `MAX_ACTIVE_API_KEYS_PER_USER`
- `MAX_TOTAL_API_KEYS_PER_USER`
- `DATABASE_URL`
- `DATABASE_AUTO_CREATE`
- `SUPABASE_URL`
- `SUPABASE_JWT_AUDIENCE`
- `SUPABASE_JWT_ISSUER`
- `SUPABASE_JWKS_CACHE_SECONDS`
- `DEV_BOOTSTRAP_API_KEY_ENABLED`
- `DEV_BOOTSTRAP_API_KEY`
- `DEV_BOOTSTRAP_OWNER_ID`
- `RATE_LIMITING_ENABLED`
- `REDIS_URL`
- `DEV_RATE_LIMIT_BYPASS`
- `IP_RATE_LIMIT_PER_SECOND`
- `IP_RATE_LIMIT_PER_MINUTE`
- `METRICS_ENABLED`
- `METRICS_PATH`
- `METRICS_TOKEN`
- `METRICS_TOKEN_HEADER`
- `REQUEST_ID_HEADER`

Security defaults and guardrails:

- `ALLOW_ORIGINS=*` is accepted only for `APP_ENV=development`.
- In `APP_ENV=development`, localhost origins are auto-allowlisted by default when `ALLOW_ORIGINS` is explicit (set `DEV_CORS_ALLOW_LOCALHOST=false` to disable).
- `staging`/`production` require explicit CORS allowlists.
- `staging`/`production` fail closed when Redis is unavailable for rate enforcement.
- `staging`/`production` require `METRICS_TOKEN` when metrics are enabled.
- `staging`/`production` require `DATABASE_AUTO_CREATE=false`.
- `staging`/`production` require `API_KEY_HASH_SECRET` to be rotated from dev default.
- Active API key creation is capped per owner by `MAX_ACTIVE_API_KEYS_PER_USER`.
- Total API key history per owner (active + revoked + rotated) is capped by `MAX_TOTAL_API_KEYS_PER_USER`.

## Operations and SLOs

- SLO and alert definitions: `docs/operations/slo.md`
- Prometheus alert rule examples: `docs/operations/alerts.prometheus.yml`
- Staging deployment playbook: `docs/operations/deploy-staging.md`
- Production deployment playbook: `docs/operations/deploy-production.md`
- Supabase Phase 3.5 schema script (includes `pgcrypto`, RLS, and owner policies): `docs/operations/phase3_5_supabase_schema.sql`

## Identerest Rollout (Phase 3.75)

1. Point `SUPABASE_URL` and `DATABASE_URL` at the Identerest Supabase project.
   - If using Supabase pooler (`*.pooler.supabase.com:6543`) with `asyncpg`, statement cache is auto-disabled by the service bootstrap for PgBouncer compatibility.
2. Apply `docs/operations/phase3_5_supabase_schema.sql` in that project.
3. Ensure OAuth providers and redirect URLs are configured for portfolio login.
4. Keep `/v1/keys*` on bearer JWT and runtime `/v1/*` on `X-API-Key` (already enforced in middleware).
5. Restart service and validate create/list/revoke/rotate flows.
6. For BYO IBM rollout, also set `IBM_CREDENTIAL_ENCRYPTION_KEY`, apply the updated Phase 3.5 schema script, and validate `/v1/ibm/profiles*` plus `/v1/jobs*`.

## BYO IBM Live Verification

Use the reusable Phase 4 smoke verifier to validate the real BYO IBM flow end-to-end with a live bearer JWT and live IBM credentials.

```bash
export VERIFY_API_BASE_URL=https://davidjgrimsley.com/public-facing/api/quantum
export VERIFY_BEARER_JWT=<supabase_jwt>
export VERIFY_IBM_TOKEN=<ibm_api_token>
export VERIFY_IBM_INSTANCE=<ibm_instance_or_crn>
export VERIFY_IBM_CHANNEL=ibm_quantum_platform

uv run python scripts/verify_byo_ibm_flow.py --timeout-seconds 1800
```

Notes:

- `VERIFY_API_BASE_URL` may be the service root or the full `/v1` base URL. The script appends `/v1` when missing.
- `IBM_CREDENTIAL_ENCRYPTION_KEY` must already be configured on the deployed server for stored-profile verification to work.
- Use `--backend-name <backend>` to force a specific IBM backend.
- Cleanup is enabled by default. Use `--no-cleanup` if you want to inspect the created verification resources afterward.
- A passing run proves: IBM profile save + verify, Quantum API key creation, IBM backend listing, IBM transpile, hardware job submission, and a terminal result or structured provider error.
- Record the run date, environment, backend, terminal job status, result/error artifact, and cleanup outcome in your release notes or roadmap notes.

## Docker

```bash
docker build -t quantum-api .
docker run --rm -p 8000:8000 quantum-api
```

## Tests and Lint

```bash
uv run ruff check .
uv run pytest
```

Tooling note:

- This repo assumes `uv` for Python workflows.
- JS SDK verification also needs Node.js, npm, and the TypeScript toolchain.
- Engine deliverables require their native toolchains for real packaging validation.

Optional performance benchmarks (non-blocking, not run in CI by default):

```bash
RUN_PERF_BENCHMARKS=true uv run pytest tests/perf -s
```

## Repository Layout

- `src/quantum_api/` - backend app, routers, models, services
- `tests/` - contract, unit, determinism, and validation tests
- `sdk/js/` - TypeScript SDK package-ready client work
- `sdk/python/` - Python SDK package-ready client work
- `sdk/godot/` - promoted reusable Godot addon/client for runtime `/v1` integration
- `sdk/unreal/` - Unreal runtime plugin scaffold for the gameplay subset
- `docs/sdk/` - SDK release governance and compatibility tracking
- `docs/migrations/` - external client migration plans (Godot, Expo, Unreal, Unity)
- `project/` - planning, style, and implementation docs

## Roadmap Status

1. Phase 1 delivered: multi-qubit execution (`/v1/circuits/run`) with strict limits.
2. Phase 2 delivered: backend discovery + transpilation + QASM interop.
3. Phase 3 delivered: production auth/rate-limiting/observability hardening.
4. Phase 4 delivered: BYO IBM runtime profiles and hardware-job lifecycle.
5. Phase 5 delivered: expanded Qiskit domain coverage across algorithms, optimization, experiments, finance, ML, and nature.
6. Current engineering focus: Phase 6 SDK productization, Godot migration, and follow-on engine integrations.

## Client Packaging

- `sdk/js/` is the package that would become the published npm package later in the roadmap.
- `sdk/python/` is the package that would become the published PyPI package later in the roadmap.
- `sdk/godot/` and `sdk/unreal/` are engine-specific delivery artifacts, not npm packages.

## License

Apache-2.0.
