# Quantum API

Quantum API is a greenfield FastAPI service for quantum-inspired runtime features:

- `/v1/health`
- `/v1/echo-types`
- `/v1/gates/run`
- `/v1/circuits/run`
- `/v1/list_backends`
- `/v1/transpile`
- `/v1/qasm/import`
- `/v1/qasm/export`
- `/v1/text/transform`
- `/v1/keys`
- `/v1/keys/{key_id}/revoke`
- `/v1/keys/{key_id}/rotate`
- `/metrics` (internal metrics endpoint)

This repository is intentionally not backward compatible with the previous `public-facing/api/quantum/*` paths.

## Tech Stack

- Python 3.11+
- FastAPI + Uvicorn
- Pydantic v2
- Redis (rate limiting and quotas)
- Prometheus client metrics
- Optional qiskit/qiskit-aer runtime (with classical fallback mode)
- Optional qiskit-ibm-runtime integration for IBM backend discovery
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

## API Contract

### Authentication and Rate Limits

- `GET /v1/health` is public.
- `GET /v1/keys`, `POST /v1/keys`, `POST /v1/keys/{key_id}/revoke`, and `POST /v1/keys/{key_id}/rotate` require `Authorization: Bearer <supabase_jwt>`.
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

### `GET /v1/echo-types`
Lists canonical transformation categories and descriptions from one enum source.

### Key Management Endpoints (`/v1/keys*`)

- `GET /v1/keys`: list current user's keys (masked metadata only).
- `POST /v1/keys`: create a key and return the raw key exactly once.
- `POST /v1/keys/{key_id}/revoke`: revoke an existing key.
- `POST /v1/keys/{key_id}/rotate`: atomically rotate key (old key becomes invalid, new raw key shown once).

All key-management endpoints are user-scoped to the JWT subject (`sub`) and require a valid Supabase bearer token.

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

Response fields:

- `backends`: list of backend summaries (`name`, `provider`, `is_simulator`, `is_hardware`, `num_qubits`, `basis_gates`, `coupling_map_summary`)
- `total`
- `filters_applied`
- `warnings` (optional, e.g. IBM provider unavailable when not explicitly requested)

Aer notes:

- The API lists modern `aer_simulator*` backends.
- Legacy aliases (`qasm_simulator`, `statevector_simulator`, `unitary_simulator`) are intentionally not exposed.

If `provider=ibm` and IBM integration is not configured, the API returns:

```json
{
  "error": "provider_unavailable",
  "message": "Provider 'ibm' is unavailable.",
  "details": {
    "reason": "missing_credentials"
  }
}
```

### `POST /v1/transpile`
Request accepts exactly one input source:

- `circuit` (JSON operation format), or
- `qasm` (`source`, `qasm_version` = `auto|2|3`)

Plus:

- `backend_name` (required)
- `provider` (`aer|ibm`, optional)
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
- `REQUEST_TIMEOUT_SECONDS`
- `REQUIRE_QISKIT`
- `IBM_TOKEN` (optional)
- `IBM_INSTANCE` (optional)
- `IBM_CHANNEL` (optional, default `ibm_quantum`)
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
- `staging`/`production` require explicit CORS allowlists.
- `staging`/`production` fail closed when Redis is unavailable for rate enforcement.
- `staging`/`production` require `METRICS_TOKEN` when metrics are enabled.
- `staging`/`production` require `DATABASE_AUTO_CREATE=false`.
- `staging`/`production` require `API_KEY_HASH_SECRET` to be rotated from dev default.

## Operations and SLOs

- SLO and alert definitions: `docs/operations/slo.md`
- Prometheus alert rule examples: `docs/operations/alerts.prometheus.yml`
- Staging deployment playbook: `docs/operations/deploy-staging.md`
- Production deployment playbook: `docs/operations/deploy-production.md`
- Supabase Phase 3.5 schema script: `docs/operations/phase3_5_supabase_schema.sql`

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

Optional performance benchmarks (non-blocking, not run in CI by default):

```bash
RUN_PERF_BENCHMARKS=true uv run pytest tests/perf -s
```

## Repository Layout

- `src/quantum_api/` - backend app, routers, models, services
- `tests/` - contract, unit, determinism, and validation tests
- `sdk/js/` - TypeScript SDK scaffold
- `sdk/python/` - Python SDK scaffold
- `docs/migrations/` - external client migration plans (Godot, Expo, Unreal, Unity)
- `project/` - planning, style, and implementation docs

## Roadmap (Phase 1-2 Delivered)

1. Core power API for multi-qubit circuit execution (`/v1/circuits/run`) is delivered with strict limits.
2. Phase 2 compilation and backend discovery endpoints are delivered (`/v1/transpile`, `/v1/list_backends`).
3. QASM interop is delivered (`/v1/qasm/import`, `/v1/qasm/export`).
4. Next major focus is Phase 3 security and production hardening.

## License

Apache-2.0.
