# Quantum API — Troubleshooting Guide

---

## Runtime Modes

The API operates in one of two modes, reported in `GET /v1/health`:

| `runtime_mode` | Meaning |
|---|---|
| `"qiskit"` | Full Qiskit simulation available |
| `"classical-fallback"` | Qiskit not installed; math-backed simulation used instead |

**Important**: `/v1/circuits/run` **always requires Qiskit** and returns `503` when it is unavailable, regardless of `REQUIRE_QISKIT` config. All other endpoints function in classical-fallback mode.

Set `REQUIRE_QISKIT=true` (server env var) to force `503` responses for all runtime endpoints when Qiskit is unavailable.

---

## Common Errors

### `503 Service Unavailable`

**`qiskit_unavailable`** — Qiskit is not installed on the server.
- For `/v1/circuits/run`: always fails without Qiskit.
- For other endpoints: only fails if `REQUIRE_QISKIT=true`.
- Fix: install Qiskit on the server (`uv sync` with Qiskit extras).

**`feature_unavailable`** — A Phase 5 domain endpoint was called but the required extra is not installed.
- Fix: install the relevant extra (see [domain-endpoints.md](./domain-endpoints.md)).

---

### `422 Unprocessable Entity`

Validation error from Pydantic. Check:
- You sent both `circuit` and `qasm` in a `/v1/transpile` request (only one allowed).
- A required field is missing (e.g., `theta` for `ry` gate, `control` for `cx`).
- A gate name is not in the supported set: `x`, `z`, `h`, `ry`, `cx`.
- A qubit index is out of range `[0, num_qubits - 1]`.
- `gate_type` for `/v1/gates/run` is not `bit_flip`, `phase_flip`, or `rotation`.
- `rotation_angle_rad` is missing when `gate_type == "rotation"`.

---

### `401 Unauthorized`

- `X-API-Key` header is missing or the key is invalid/revoked/rotated-away.
- `Authorization: Bearer` JWT is missing, expired, or invalid for key-management endpoints.
- The dev bootstrap key (`qapi_devlocal_...`) is being used on a non-development server.

---

### `403 Forbidden`

- The API key does not have permission to access the requested resource (keys are user-scoped).
- JWT `sub` does not match the owner of the requested key or IBM profile.

---

### `429 Too Many Requests`

```json
{
  "error": "too_many_requests",
  "message": "Rate limit or quota exceeded.",
  "details": {
    "policy": "key_minute",
    "retry_after_seconds": 15
  },
  "request_id": "..."
}
```

- Check `Retry-After` response header for the exact wait time.
- `policy` values: `key_second`, `key_minute`, `key_daily`, `ip_second`, `ip_minute`.
- Daily quota resets at midnight UTC.
- In staging/production, rate limiting fails **closed** when Redis is unavailable — all requests are rejected until Redis recovers.

---

### IBM Provider Errors

**`provider_credentials_missing`**:
```json
{
  "error": "provider_credentials_missing",
  "message": "IBM provider credentials are not configured for this user."
}
```
- The user has no saved IBM profile and the server has no fallback `IBM_TOKEN`.
- Fix: create an IBM profile via `POST /v1/ibm/profiles` and verify it.

**`result_not_ready`** (on `GET /v1/jobs/{job_id}/result`):
```json
{
  "error": "result_not_ready",
  "message": "Job 'job-id' has not produced a result yet.",
  "details": { "job_id": "job-id", "status": "running" }
}
```
- The IBM hardware job is still queued or running.
- Poll `GET /v1/jobs/{job_id}` until `status` is `succeeded` or `failed`, then fetch the result.

---

### QASM 3 Issues

**`qasm3_dependency_missing`** — `qiskit_qasm3_import` is not installed.
- QASM 3 import is **best-effort**. Fall back to QASM 2 if this error appears.
- QASM 3 export works independently of this dependency.

---

## CORS Errors (Browser / Expo)

- `ALLOW_ORIGINS=*` is only accepted in `APP_ENV=development`.
- In staging/production, CORS requires an explicit allowlist in `ALLOW_ORIGINS`.
- For local dev, `DEV_CORS_ALLOW_LOCALHOST=true` (default) auto-allowlists localhost origins.
- If calling from a browser in production, ensure your origin is in the server's `ALLOW_ORIGINS`.

---

## Rate Limit Header Inspection

Always inspect rate-limit headers on successful responses to implement proper backoff:

```
RateLimit-Limit: 100
RateLimit-Remaining: 87
RateLimit-Reset: 1748800000
```

Implement exponential backoff with jitter for `429` responses. Use the `Retry-After` header value as the minimum wait.

---

## Verifying End-to-End with the BYO IBM Smoke Verifier

For full end-to-end verification of the IBM flow (profiles, keys, transpile, hardware job), use the built-in smoke verifier:

```bash
export VERIFY_API_BASE_URL=https://davidjgrimsley.com/public-facing/api/quantum
export VERIFY_BEARER_JWT=<supabase_jwt>
export VERIFY_IBM_TOKEN=<ibm_api_token>
export VERIFY_IBM_INSTANCE=<ibm_instance_or_crn>
export VERIFY_IBM_CHANNEL=ibm_quantum_platform

uv run python scripts/verify_byo_ibm_flow.py --timeout-seconds 1800
```

A passing run validates: IBM profile save + verify, API key creation, IBM backend listing, transpile, hardware job submission, terminal result or structured provider error, and cleanup.
