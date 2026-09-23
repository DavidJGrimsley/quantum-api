# Quantum API — Troubleshooting Guide

---

## Runtime Modes

The API operates in one of two modes, reported in `GET /v1/health`:

| `runtime_mode` | Meaning |
|---|---|
| `"qiskit"` | Full Qiskit simulation available |
| `"classical-fallback"` | Qiskit not installed; math-backed simulation used instead |

`/v1/circuits/run`, `/v1/list_backends`, `/v1/transpile`, and all
`/v1/qasm/*` routes require base Qiskit and return `503` without it.
`/v1/gates/run`, `/v1/random`, and `/v1/text/transform` can use the
classical fallback unless the server sets `REQUIRE_QISKIT=true`. Phase 5
domain routes also require their respective optional dependencies. Health
reports base Qiskit availability, not the availability of those extras.

---

## Common Errors

### `503 Service Unavailable`

**Base Qiskit unavailable** — `/v1/list_backends`, `/v1/transpile`, and
`/v1/qasm/*` return `error: "provider_unavailable"` with status `503`.
`/v1/circuits/run` returns `503` with `error: "service_unavailable"`.
The fallback-capable core routes return that same error only when
`REQUIRE_QISKIT=true`. Read the response's `message` and ask the server
owner to install or enable Qiskit.

**`provider_unavailable`** — A Phase 5 domain endpoint's required dependency
is absent. Check `details.reason` for `missing_dependency` and ask the server
owner to install the relevant extra (see [domain-endpoints.md](./domain-endpoints.md)).

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
- The dev bootstrap key (`qapi_devlocal_...`) is being used on a non-development server.

---

### `403 Forbidden`

- The API key does not have permission to access the requested resource (keys are user-scoped).

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
- Ask the owner for an existing IBM profile name or to configure access.

**`result_not_ready`** (on `GET /v1/jobs/{job_id}/result`):
```json
{
  "error": "result_not_ready",
  "message": "Job 'job-id' has not produced a result yet.",
  "details": { "job_id": "job-id", "status": "running" }
}
```
- Poll `GET /v1/jobs/{job_id}` until a terminal status. Fetch the result
  only when `status` is `succeeded`; for `failed` or `cancelled`, inspect
  the status and any `error` in that response instead. `result_not_ready` can occur for
  any status other than `succeeded`.

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
RateLimit-Reset: 42
```

`RateLimit-Reset` is seconds until the current window resets. Implement
exponential backoff with jitter for `429` responses. Use the `Retry-After`
header value as the minimum wait.

---
