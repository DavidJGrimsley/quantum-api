# Quantum API — Agent Integration Instructions

You are integrating the Quantum API into a user's project.

**API v1 base URL (production)**: `https://davidjgrimsley.com/public-facing/api/quantum/v1`  
**Interactive docs**: `https://davidjgrimsley.com/public-facing/api/quantum/docs`  
**Machine-readable facts**: [`manifest.json`](./manifest.json)

---

## Before Making Changes

1. **Determine the integration target**: browser/Node TypeScript, Python script/notebook, PennyLane, Unreal Engine, Unity, Godot, or raw HTTP.
2. **Determine the auth context**: Does the user have an `X-API-Key`? Do they need to create one (requires Supabase bearer JWT)? Are they submitting IBM hardware jobs (requires a saved IBM profile)?
3. **Determine the execution model**: Synchronous local simulation (`/v1/circuits/run`, `/v1/qasm/run`) or asynchronous IBM hardware jobs (`/v1/jobs/*`)?
4. **Check Phase 5 availability**: Domain algorithm endpoints (optimization, experiments, finance, ML, nature) require server-side extras. Verify with `GET /v1/health`.
5. **Do not invent API names, fields, or endpoints.** Use only what is in the documentation hierarchy below.
6. **Prefer examples from this documentation over inferred usage.**

---

## Documentation Hierarchy

For authentication and key management:
→ [`skills/quantum-api/references/authentication.md`](./skills/quantum-api/references/authentication.md)

For endpoint signatures, request/response shapes, error envelope:
→ [`skills/quantum-api/references/api-contract.md`](./skills/quantum-api/references/api-contract.md)

For SDK-specific installation and usage:
→ [`skills/quantum-api/references/sdks.md`](./skills/quantum-api/references/sdks.md)

For Phase 5 domain endpoints (optimization, experiments, finance, ML, nature):
→ [`skills/quantum-api/references/domain-endpoints.md`](./skills/quantum-api/references/domain-endpoints.md)

For errors, runtime modes, and IBM issues:
→ [`skills/quantum-api/references/troubleshooting.md`](./skills/quantum-api/references/troubleshooting.md)

For detailed per-domain algorithm docs:
→ [`docs/domains/`](./docs/domains/)

---

## When Information Is Missing

If the documentation does not specify a behavior, field, or endpoint, say so
rather than inventing an implementation. The Quantum API contract is intentionally
strict — guessing at undocumented fields will produce validation errors.

---

## Verification Steps

After completing an integration, verify:

1. `GET /v1/health` returns `{"status": "ok"}` with `qiskit_available` and `runtime_mode`.
2. A protected endpoint returns `X-Request-ID`, `RateLimit-Limit`, `RateLimit-Remaining` headers.
3. An error response (e.g., from a bad request) matches the normalized error envelope:
   `{"error": "...", "message": "...", "details": {...}, "request_id": "..."}`.
4. For IBM hardware jobs: `GET /v1/jobs/{job_id}` returns a normalized `status` value (`queued` | `running` | `succeeded` | `failed` | `cancelling` | `cancelled`).

---

## Version Policy

- All endpoints are under `/v1`. Do not use any other prefix.
- The API is **not backward compatible** with the previous `public-facing/api/quantum/*` paths.
- QASM 3 import is best-effort. Fall back to QASM 2 if `qasm3_dependency_missing` is returned.
- IBM hardware job submission supports `provider: "ibm"` only in the current contract.
- The dev bootstrap key `qapi_devlocal_0123456789abcdef0123456789abcdef` works only when `APP_ENV=development` on the server.

---

## Agent Skill Install

This file is the root-level agent contract. The full installable skill is at
[`skills/quantum-api/SKILL.md`](./skills/quantum-api/SKILL.md).

To install globally for supported coding agents (Antigravity, Cursor, Codex):

```bash
npx skills add -g davidjgrimsley/quantum-api
```

