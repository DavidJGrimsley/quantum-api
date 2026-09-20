---
name: quantum-api
description: >-
  Use this skill when the user wants to integrate, call, or work with the
  Quantum API (davidjgrimsley/quantum-api) — a FastAPI service for quantum-
  inspired runtime features including circuit execution, QASM interop,
  transpilation, IBM hardware job submission, key management, and domain
  algorithms (optimization, experiments, finance, ML, nature). Also activate
  when the user mentions any Quantum API SDK (JavaScript/TypeScript, Python,
  PennyLane, Unreal Engine, Unity, Godot), asks to "add the Quantum API",
  "submit a quantum circuit", "run QASM", "connect to IBM quantum hardware",
  or wants to manage Quantum API keys or IBM credential profiles.
---

# Quantum API — Agent Skill

**Product**: Quantum API by David J. Grimsley  
**Current version**: 0.1.x (API), 0.1.2 (JS SDK), 0.1.0 (Python/Unreal/Unity/Godot/PennyLane)  
**Service root (production)**: `https://davidjgrimsley.com/public-facing/api/quantum`  
**API v1 base (production)**: `https://davidjgrimsley.com/public-facing/api/quantum/v1`  
**Local dev URL**: `http://127.0.0.1:8000` (endpoints at `http://127.0.0.1:8000/v1/...`)  
**Docs**: `https://davidjgrimsley.com/public-facing/api/quantum/docs`  
**Repo**: `https://github.com/davidjgrimsley/quantum-api`

---

## Before Making Any Changes

1. Determine the **integration target** (browser/Node JS, Python script, Unreal game, Unity game, Godot game, PennyLane circuit).
2. Determine whether the user needs **synchronous execution** (`/v1/circuits/run`, `/v1/qasm/run`) or **async hardware jobs** (`/v1/jobs/*`).
3. Determine the **auth context**: does the user have an API key (`X-API-Key`) or a Supabase bearer JWT?  
   - Key management and IBM profiles require a bearer JWT.  
   - All other runtime endpoints require an API key.
4. **Do not invent API names, endpoints, or parameter names.** Use only what is in the reference files.

---

## Documentation Hierarchy

Read these references in order of relevance to the task:

| Reference | When to read |
|---|---|
| [api-contract.md](./references/api-contract.md) | Every integration task — full endpoint list, request/response shapes, error envelope |
| [authentication.md](./references/authentication.md) | Auth setup, key creation, IBM profiles, Supabase JWT |
| [sdks.md](./references/sdks.md) | When using JS SDK, Python SDK, PennyLane, Unreal, Unity, or Godot |
| [domain-endpoints.md](./references/domain-endpoints.md) | Optimization, experiments, finance, ML, or nature domain endpoints |
| [troubleshooting.md](./references/troubleshooting.md) | Errors, 503 responses, qiskit availability, rate limit handling |

---

## Integration Checklist

### Step 1 — Choose the right entry point

| Target | Recommended client |
|---|---|
| TypeScript / Expo / browser | JS SDK (`@mr.dj2u/quantum-api`) or raw `fetch` |
| Python script / notebook | Python SDK (`quantum-api-sdk`) or `httpx` |
| PennyLane circuit | PennyLane plugin (`quantum-api-pennylane`, device `quantum.api`) |
| Unreal Engine 5.x | Unreal plugin (`sdk/unreal/`) — HTTP, not Unreal Python |
| Unity | Unity helper (`sdk/unity/`) |
| Godot 4.x | Godot addon (`sdk/godot/`) |
| Raw HTTP / cURL | See [api-contract.md](./references/api-contract.md) |

### Step 2 — Obtain credentials

- **API key**: Create via `POST /v1/keys` (requires Supabase bearer JWT). See [authentication.md](./references/authentication.md).
- **Dev key**: Use `qapi_devlocal_0123456789abcdef0123456789abcdef` against a local dev server only.
- **IBM hardware**: Save a profile via `POST /v1/ibm/profiles`, then reference it by name.

### Step 3 — Implement the call

Use the reference files for exact request/response shapes. Never guess field names.

### Step 4 — Verify

After integration, confirm:
1. `GET /v1/health` returns `{"status": "ok"}` with `qiskit_available` and `runtime_mode`.
2. A guarded endpoint returns `X-Request-ID`, `RateLimit-Limit`, `RateLimit-Remaining`.
3. Error responses match the normalized envelope: `{"error": "...", "message": "...", "details": {...}, "request_id": "..."}`.

---

## When Information Is Missing

- If an endpoint, field, or behavior is not described in the reference files, say so rather than inventing an implementation.
- If you are unsure whether a feature is available (e.g., Phase 5 domain endpoints), check [domain-endpoints.md](./references/domain-endpoints.md) for the required extras and availability.

---

## Version Policy

- The API contract is intentionally **not backward compatible** with the previous `public-facing/api/quantum/*` paths.
- `/v1` is the current canonical prefix. Do not use any other prefix.
- QASM 3 import is best-effort; fallback to QASM 2 if `qasm3_dependency_missing` is returned.
- IBM hardware job support is `provider: "ibm"` only in the current job submission API.

