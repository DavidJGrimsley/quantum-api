---
name: quantum-api
description: >-
  Integrate the Quantum API into apps, games, scripts, and PennyLane circuits.
  Use for its REST runtime, local or IBM random jobs, QASM, domain algorithms,
  and first-party JavaScript, Python, Unreal, Unity, and Godot clients.
---

# Quantum API integration

The production API v1 base is `https://davidjgrimsley.com/public-facing/api/quantum/v1`.
For a local server, use `http://127.0.0.1:8000/v1`. Append endpoint paths
such as `/random` to one of these bases; do not add `/v1` twice.

## Choose the integration path

- For REST request and response shapes, read [api-contract.md](references/api-contract.md).
- For a client library or game engine, read [sdks.md](references/sdks.md).
- For optimization, experiments, finance, ML, or nature, read [domain-endpoints.md](references/domain-endpoints.md).
- For errors, runtime modes, and retries, read [troubleshooting.md](references/troubleshooting.md).
- For runtime credentials, read [authentication.md](references/authentication.md).

Use the user's integration target and execution need to choose between a
synchronous runtime call and an asynchronous IBM hardware job. Check the
current OpenAPI schema or source when a reference is incomplete or a version
may have changed. Do not invent endpoint or SDK method names.

## Credentials and owner-only operations

Runtime calls use a supplied `X-API-Key`. Ask the user for an existing key or
for a backend proxy; never ask for a login session token. For IBM hardware,
use a profile name supplied by the user, or their existing default profile.
Keep API keys out of distributed browser and game builds by using a backend
proxy.

API-key lifecycle and IBM credential-profile management are administrative
operations reserved for the owner. Do not create, list, rotate, revoke, delete,
or verify those records, and do not guide an integration user through those
operations. If a required key or profile is missing, ask the owner to supply
it through their administrative process. This restriction does not prevent
runtime calls that use an existing key or profile name.

## Runtime distinctions

- `POST /v1/random` returns one inclusive-range local integer. Its
  `qiskit-simulator` and `classical-fallback` sources are not cryptographic
  randomness or IBM hardware entropy.
- `POST /v1/jobs/random` submits an IBM hardware job. Poll the job status and
  result routes; an `ibm-hardware` source is not a cryptographic guarantee.
- `POST /v1/circuits/run` and `POST /v1/qasm/run` are synchronous simulator
  calls. IBM circuit and QASM jobs use the asynchronous `/v1/jobs/*` routes.
- The server may return `503` when Qiskit or an optional domain extra is
  unavailable. Check `GET /v1/health` before diagnosing runtime capability.

## Verify an integration

`GET /v1/health` is public and reports `status: "healthy"`,
`qiskit_available`, and `runtime_mode`. `GET /v1/echo-types` and protected
runtime endpoints require an API key. Successful protected responses include
`X-Request-ID` and rate-limit headers. Errors use an `error`, `message`,
`details`, and `request_id` envelope. For hardware work, verify a terminal job
status and fetch the result; job submission alone is not proof of execution.

The `/v1` routes are the current contract. QASM 3 import is best effort; use
QASM 2 if `qasm3_dependency_missing` is returned.
