# Compatibility Matrix

This matrix tracks first-party client readiness against the current `Quantum API /v1` surface.

| Client | Status | Supported surface | Auth modes | Notes |
|---|---|---|---|---|
| API `/v1` | Active | Full current contract | Public, `X-API-Key` | Canonical server contract |
| JS SDK | 0.1.2 on npm | Core, jobs, QASM, domains; QRNG via HTTP | `X-API-Key`, per-request override | Browser, Node, Expo |
| Python SDK | 0.1.0 on PyPI | Core, jobs, QASM, domains; QRNG via HTTP | `X-API-Key`, per-call override | Synchronous client |
| PennyLane plugin | 0.1.0 on PyPI | `/v1/qasm/run` (finite shots or analytic statevector) | `X-API-Key` | Device `quantum.api` |
| Godot addon/client | 0.1.2 reusable addon | Health, text, gates, backends, transpile, IBM circuit jobs | Proxy or direct development key | Runtime node with optional editor settings helper |
| Unreal plugin | 0.3.0-beta, UE 5.8 Win64 | Core, QRNG, IBM jobs, allowlisted advanced routes | Proxy or direct development key | UEFN unsupported |
| Unity client | 0.1.0 repo-local package | Health, echo, gates, text, local QRNG, IBM random jobs | Proxy or direct development key | Shared manager 0.2.0 remains pending in PR #19 |

## Update rules

- Mark a client `package-ready` only after its package/plugin metadata, docs, and smoke coverage are in place.
- Mark a client `published` only after external distribution actually happens.
- When the API adds a new endpoint group, update this matrix and each client README to reflect support status.
