# Quantum API — Core REST API Contract

**Service root (production)**: `https://davidjgrimsley.com/public-facing/api/quantum`  
**API v1 base (production)**: `https://davidjgrimsley.com/public-facing/api/quantum/v1`  
**Local dev API v1 base**: `http://127.0.0.1:8000/v1`  
Endpoint headings use canonical `/v1/...` paths. If a client is configured
with the API v1 base, append only the suffix after `/v1`. Full example:
`POST https://davidjgrimsley.com/public-facing/api/quantum/v1/circuits/run`.

---

## Authentication Summary

| Endpoint group | Auth required |
|---|---|
| `GET /v1/health`, `GET /v1/portfolio.json` | None (public) |
| Other documented `/v1/*` endpoints | `X-API-Key: <key>` header |

---

## Standard Response Headers (protected endpoints)

Successful responses on protected endpoints include:

```
X-Request-ID: <uuid>
RateLimit-Limit: <n>
RateLimit-Remaining: <n>
RateLimit-Reset: <unix_timestamp>
```

`429` responses also include `Retry-After: <seconds>`.

---

## Error Envelope (all errors)

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

Always check `error` (machine code) + `message` (human text) + `details` (context).

---

## Endpoint Reference

### `GET /v1/health`
**Auth**: None

**Response**:
```json
{
  "status": "healthy",
  "service": "Quantum API",
  "version": "0.1.0",
  "qiskit_available": true,
  "runtime_mode": "qiskit"
}
```

`runtime_mode` is either `"qiskit"` (full simulation) or `"classical-fallback"` (math-backed).

---

### `GET /v1/portfolio.json`
**Auth**: None

Public metadata contract. Lists discoverable endpoints with their `path`, `operationPath`, `method`, and auth classification (`public` | `api_key`). Used by portfolio pages and app integrations.

---

### `GET /v1/echo-types`
**Auth**: `X-API-Key`

Returns canonical transformation categories and descriptions for the `/v1/text/transform` endpoint.

---

### `POST /v1/random`
**Auth**: `X-API-Key`

Generates one local integer in an inclusive range:

```json
{"min": 0, "max": 1}
```

```json
{"value": 1, "source": "qiskit-simulator"}
```

Both bounds must be JSON integers within signed 32-bit range, with `min <= max`.
Extra fields and non-integer bounds return `422`. The source can be
`qiskit-simulator` or `classical-fallback`. Both are local simulation and
neither provides IBM hardware entropy or cryptographic randomness.

---

### `POST /v1/gates/run`
**Auth**: `X-API-Key`

```json
// Request
{
  "gate_type": "rotation",       // "bit_flip" | "phase_flip" | "rotation"
  "rotation_angle_rad": 1.5708   // required only when gate_type == "rotation"
}

// Response
{
  "gate_type": "rotation",
  "measurement": 1,
  "superposition_strength": 1.0,
  "success": false
}
```

---

### `POST /v1/circuits/run`
**Auth**: `X-API-Key`  
**Note**: Always requires qiskit. Returns `503` when qiskit is unavailable.

```json
// Request
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

**Gate rules**:
- `gate`: one of `x`, `z`, `h`, `ry`, `cx`
- `target`: required for every operation
- `theta`: required only for `ry`
- `control`: required only for `cx`; must differ from `target`
- All qubit indexes must be in `[0, num_qubits - 1]`

```json
// Response
{
  "num_qubits": 2,
  "shots": 1024,
  "counts": { "00": 496, "11": 528 },
  "backend_mode": "qiskit",
  "statevector": null
}
```

`counts` keys are zero-padded bitstrings. Set `include_statevector: true` to get amplitude arrays `{"real": ..., "imag": ...}` per basis state.

---

### `GET /v1/list_backends`
**Auth**: `X-API-Key`

**Query params**:

| Param | Values | Notes |
|---|---|---|
| `provider` | `aer` \| `ibm` | |
| `simulator_only` | `true` / `false` | |
| `min_qubits` | integer ≥ 1 | |
| `ibm_profile` | profile name string | `provider=ibm` only; defaults to owner's default profile |

**Response**:
```json
{
  "backends": [
    {
      "name": "aer_simulator",
      "provider": "aer",
      "is_simulator": true,
      "is_hardware": false,
      "num_qubits": 32,
      "basis_gates": ["cx", "id", "rz", "sx", "x"],
      "coupling_map_summary": null
    }
  ],
  "total": 1,
  "filters_applied": { "provider": "aer" },
  "warnings": []
}
```

Legacy aliases (`qasm_simulator`, `statevector_simulator`, `unitary_simulator`) are not exposed — use `aer_simulator*` names.

---

### `POST /v1/transpile`
**Auth**: `X-API-Key`

Accepts exactly one of `circuit` or `qasm` (not both — sending both returns `422`).

```json
// Circuit input
{
  "circuit": {
    "num_qubits": 2,
    "operations": [{ "gate": "h", "target": 0 }, { "gate": "cx", "control": 0, "target": 1 }]
  },
  "backend_name": "aer_simulator",
  "provider": "aer",
  "optimization_level": 1,
  "seed_transpiler": 42,
  "output_qasm_version": "3"
}
```

```json
// QASM input
{
  "qasm": { "source": "OPENQASM 2.0; ...", "qasm_version": "auto" },
  "backend_name": "ibm_kingston",
  "provider": "ibm",
  "ibm_profile": "my-open-plan",
  "optimization_level": 2,
  "output_qasm_version": "3"
}
```

**Response**:
```json
{
  "backend_name": "aer_simulator",
  "provider": "aer",
  "input_format": "circuit",
  "num_qubits": 2,
  "depth": 2,
  "size": 2,
  "operations": [...],
  "qasm_version": "3",
  "qasm": "OPENQASM 3.0; ..."
}
```

---

### QASM Endpoints

#### `POST /v1/qasm/import`
**Auth**: `X-API-Key`

```json
// Request
{ "qasm": "OPENQASM 2.0; ...", "qasm_version": "auto" }

// Response
{
  "detected_qasm_version": "2",
  "num_qubits": 1,
  "depth": 1,
  "size": 1,
  "operations": [{ "gate": "h", "target": 0 }]
}
```

`qasm_version`: `"auto"` | `"2"` | `"3"`. QASM 3 import is best-effort; returns `qasm3_dependency_missing` if `qiskit_qasm3_import` is absent.

#### `POST /v1/qasm/export`
**Auth**: `X-API-Key`

```json
// Request
{
  "circuit": { "num_qubits": 2, "operations": [...] },
  "qasm_version": "3"
}

// Response
{ "qasm_version": "3", "qasm": "OPENQASM 3.0; ...", "num_qubits": 2, "depth": 2, "size": 2 }
```

Default export version is QASM 3.

#### `POST /v1/qasm/run`
**Auth**: `X-API-Key`

```json
// Request
{
  "qasm": "OPENQASM 2.0; ...",
  "qasm_version": "auto",
  "shots": 1024,
  "include_statevector": false,
  "seed": 7
}
```

Set `shots: null` for analytic mode (returns `statevector`, `counts: null`).

```json
// Response
{
  "detected_qasm_version": "2",
  "num_qubits": 2,
  "shots": 1024,
  "counts": { "00": 500, "11": 524 },
  "backend_mode": "qiskit",
  "statevector": null
}
```

---

### `POST /v1/text/transform`
**Auth**: `X-API-Key`

```json
// Request
{ "text": "memory signal and quantum circuit" }

// Response
{
  "original": "memory signal and quantum circuit",
  "transformed": "...",
  "coverage_percent": 80.0,
  "quantum_words": 4,
  "total_words": 5,
  "category_counts": {
    "scramble": 0, "reverse": 0, "ghost": 0,
    "quantum_caps": 0, "quantum_gates": 2,
    "quantum_entanglement": 0, "quantum_interference": 2,
    "original": 1
  }
}
```

---

### Hardware Job Endpoints (`/v1/jobs*`)
**Auth**: `X-API-Key`  
Jobs are scoped to the supplied API key's owner.

#### `POST /v1/jobs/circuits`
Submit async IBM hardware job from JSON circuit.

```json
{
  "provider": "ibm",
  "backend_name": "ibm_kingston",
  "shots": 1024,
  "ibm_profile": "my-open-plan",
  "circuit": {
    "num_qubits": 2,
    "operations": [{ "gate": "h", "target": 0 }, { "gate": "cx", "control": 0, "target": 1 }]
  }
}
```

#### `POST /v1/jobs/qasm`
Submit async IBM hardware job from OpenQASM source.

```json
{
  "provider": "ibm",
  "backend_name": "ibm_kingston",
  "qasm": "OPENQASM 2.0; ...",
  "qasm_version": "auto",
  "shots": 1024,
  "ibm_profile": "my-open-plan"
}
```

#### `POST /v1/jobs/random`
Submit an inclusive-range random integer job to an IBM hardware backend:

```json
{
  "min": 0,
  "max": 1,
  "provider": "ibm",
  "backend_name": "ibm_kingston",
  "ibm_profile": "supplied-profile-name"
}
```

`backend_name` is required; `ibm_profile` is optional when the owner has a
default. Bounds are signed 32-bit integers and follow the local random
endpoint's validation. Poll the common job status and result routes. A
successful result contains `{"value": 1, "source": "ibm-hardware"}`.
The source label is not a cryptographic randomness guarantee.

**Job submission returns**:
```json
{
  "job_id": "...",
  "provider": "ibm",
  "backend_name": "ibm_kingston",
  "ibm_profile": "my-open-plan",
  "status": "queued",
  "remote_job_id": "...",
  "created_at": "...",
  "updated_at": "..."
}
```

#### `GET /v1/jobs/{job_id}`
Returns job with normalized local status: `queued` | `running` | `succeeded` | `failed` | `cancelling` | `cancelled`.

#### `GET /v1/jobs/{job_id}/result`
Returns cached terminal result. If not finished:
```json
{
  "error": "result_not_ready",
  "message": "Job 'job-id' has not produced a result yet.",
  "details": { "job_id": "job-id", "status": "running" }
}
```

#### `POST /v1/jobs/{job_id}/cancel`
Attempts to cancel the remote hardware job; returns updated normalized status.

---

### `GET /metrics` (Internal)
Exposes Prometheus metrics. Requires `X-Metrics-Token` in staging/production.
