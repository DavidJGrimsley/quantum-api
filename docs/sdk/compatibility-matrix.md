# Compatibility Matrix

This matrix tracks first-party client readiness against the current `Quantum API /v1` surface.

| Client | Status | Supported surface | Auth modes | Notes |
|---|---|---|---|---|
| API `/v1` | Active | Full current contract | Public, `X-API-Key`, bearer JWT | Canonical server contract |
| JS SDK | Phase 6 package-ready target | Full `/v1` | `X-API-Key`, bearer JWT, per-request override | Primary frontend-friendly client for TS/Expo/browser usage |
| Python SDK | Phase 6 package-ready target | Full `/v1` | `X-API-Key`, bearer JWT, per-request override | Sync-first client with context-manager ergonomics |
| PennyLane plugin | Phase 6 package-ready target | `/v1/qasm/run` (finite-shot + analytic statevector mode) | `X-API-Key` by default via SDK client auth routing | Device name `quantum.api`; packaged as `quantum-api-pennylane` |
| Godot addon/client | Phase 6 reference integration | `health`, `text/transform`, `gates/run` first; expand from there | Backend proxy by default, optional direct `X-API-Key` dev mode | Mounted `/v1` base required |
| Unreal plugin | Phase 6 scaffold and follow-on integration | `health`, `text/transform`, `gates/run` first; optional `circuits/run` and `jobs/*` later | Backend proxy by default, optional direct `X-API-Key` dev mode | Packaged runtime uses HTTP, not Unreal Python |
| Unity client | Phase 6 scaffold/package-ready helper | `health`, `text/transform`, `gates/run` first; optional `circuits/run` and `jobs/*` later | Backend proxy by default, optional direct `X-API-Key` dev mode | Runtime helper scaffold added in Phase 6; Unity editor smoke test and package publishing not yet validated |

## Update rules

- Mark a client `package-ready` only after its package/plugin metadata, docs, and smoke coverage are in place.
- Mark a client `published` only after external distribution actually happens.
- When the API adds a new endpoint group, update this matrix and each client README to reflect support status.
