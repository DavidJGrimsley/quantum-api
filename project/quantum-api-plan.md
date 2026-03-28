# Quantum API Canonical Plan (Implemented Baseline)

## Objective

Deliver a greenfield Quantum API with a clean `/v1` contract, no legacy compatibility routes, and implementation-ready migration guidance for existing consumers.

## Phase 1 Deliverables

### Core API

1. `GET /v1/health`
2. `GET /v1/echo-types`
3. `POST /v1/gates/run`
4. `POST /v1/text/transform`

### Engineering Baseline

- FastAPI + Uvicorn service with typed Pydantic schemas
- Modular architecture (`api`, `models`, `services`)
- Runtime guardrails:
  - request validation
  - bounded text length
  - request timeout middleware
  - sanitized errors
- Optional qiskit runtime with explicit health reporting

### DevOps and Repo Setup

- `pyproject.toml` with uv-compatible workflow
- Ruff, Pytest, and CI in GitHub Actions
- Dockerfile and docker ignore
- Apache-2.0 license
- Root README with setup and contract docs

### SDK Scaffolding

- `sdk/js` typed TypeScript client
- `sdk/python` HTTPX Python client

### Consumer Migration Planning

- `docs/migrations/godot-game-migration.md`
- `docs/migrations/expo-animation-migration.md`
- `docs/migrations/unreal-engine-integration-plan.md`
- `docs/migrations/unity-engine-integration-plan.md`

## API Contract Notes

- Rotation uses `rotation_angle_rad` (radians only)
- No memory/speaker payload schema in Phase 1 text endpoint
- No backward compatibility aliases in API paths

## Deferred Work (Post Phase 1)

- Authentication and rate limiting
- Async execution jobs
- Advanced transpile/run-circuit endpoints
- Domain-specific algorithm endpoints

## Phase 2 - Engine Client Strategy

### Godot Reusable Addon/Client

- Build a reusable Godot addon (`addons/quantum_api_client/`) so multiple games can share one integration.
- Expose a small API surface:
  - `health_check()`
  - `run_gate(gate_type, rotation_angle_rad)`
  - `transform_text(text)`
  - `get_echo_types()`
- Centralize base URL, endpoint paths, timeouts, and fallback behavior.
- Keep game scripts focused on narrative/gameplay logic instead of HTTP plumbing.

### Unreal Engine Integration Track

- Add a dedicated Unreal client plan for runtime API calls using Unreal HTTP systems (C++/Blueprint).
- Treat Unreal Python as editor automation only, not gameplay runtime.
- Deliver an Unreal client wrapper design that maps to the same `/v1` contract used by Godot/Expo.

### Unity Engine Integration Track

- Add a dedicated Unity client plan for runtime API calls using `UnityWebRequest`.
- Deliver a reusable C# client wrapper that maps to the same `/v1` contract.
- Support async request flow and graceful offline fallbacks in gameplay logic.
