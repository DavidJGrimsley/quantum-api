# Quantum API

Quantum API is a greenfield FastAPI service for quantum-inspired runtime features:

- `/v1/health`
- `/v1/echo-types`
- `/v1/gates/run`
- `/v1/text/transform`

This repository is intentionally not backward compatible with the previous `public-facing/api/quantum/*` paths.

## Tech Stack

- Python 3.11+
- FastAPI + Uvicorn
- Pydantic v2
- Optional qiskit/qiskit-aer runtime (with classical fallback mode)
- Ruff + Pytest
- Docker
- GitHub Actions CI

## Quickstart (uv)

```bash
uv sync --extra dev
uv run uvicorn quantum_api.main:app --reload
```

Open docs at `http://127.0.0.1:8000/docs`.

## API Contract

### `GET /v1/health`
Response fields:

- `status`
- `service`
- `version`
- `qiskit_available`
- `runtime_mode`

### `GET /v1/echo-types`
Lists canonical transformation categories and descriptions from one enum source.

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

## Runtime Modes

- `qiskit`: qiskit imports are available.
- `classical-fallback`: qiskit imports are unavailable; math-backed simulation is used.

Set `REQUIRE_QISKIT=true` to force 503 responses for runtime endpoints when qiskit is unavailable.

## Configuration

Copy `.env.example` to `.env` and adjust values as needed.

- `APP_ENV`
- `API_PREFIX`
- `MAX_TEXT_LENGTH`
- `ALLOW_ORIGINS`
- `REQUEST_TIMEOUT_SECONDS`
- `REQUIRE_QISKIT`

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

## Repository Layout

- `src/quantum_api/` - backend app, routers, models, services
- `tests/` - contract, unit, determinism, and validation tests
- `sdk/js/` - TypeScript SDK scaffold
- `sdk/python/` - Python SDK scaffold
- `docs/migrations/` - external client migration plans (Godot, Expo, Unreal, Unity)
- `project/` - planning, style, and implementation docs

## Roadmap (Phase 1)

1. Complete core `/v1` runtime and validations.
2. Stabilize transformation behavior and category strategy.
3. Publish initial SDK packages.
4. Execute Godot, Expo, Unreal, and Unity migration plans from `docs/migrations/`.

## License

Apache-2.0.
