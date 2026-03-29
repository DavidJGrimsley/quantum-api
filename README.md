# Quantum API

Quantum API is a greenfield FastAPI service for quantum-inspired runtime features:

- `/v1/health`
- `/v1/echo-types`
- `/v1/gates/run`
- `/v1/circuits/run`
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

### `POST /v1/circuits/run`
Request (Bell circuit example):

```json
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

Operation rules:

- `gate` must be one of `x`, `z`, `h`, `ry`, `cx`
- `target` is required for every operation
- `theta` is required only for `ry`
- `control` is required only for `cx`
- `control` and `target` must be different for `cx`
- qubit indexes must be in range `[0, num_qubits - 1]`

Response:

```json
{
  "num_qubits": 2,
  "shots": 1024,
  "counts": {
    "00": 496,
    "11": 528
  },
  "backend_mode": "qiskit",
  "statevector": null
}
```

Notes:

- `counts` keys are zero-padded bitstrings from qiskit simulator output.
- Use `include_statevector: true` to include serialized amplitudes (`real`, `imag`) for each basis state.
- This endpoint is qiskit-dependent and returns `503` if qiskit is unavailable.

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
`/v1/circuits/run` always requires qiskit and returns `503` when qiskit is unavailable.

## Configuration

Copy `.env.example` to `.env` and adjust values as needed.

- `APP_ENV`
- `API_PREFIX`
- `MAX_TEXT_LENGTH`
- `MAX_CIRCUIT_QUBITS`
- `MAX_CIRCUIT_DEPTH`
- `MAX_CIRCUIT_SHOTS`
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

Optional performance benchmarks (non-blocking, not run in CI by default):

```bash
RUN_PERF_BENCHMARKS=true uv run pytest tests/perf -s
```

## Repository Layout

- `src/quantum_api/` - backend app, routers, models, services
- `tests/` - contract, unit, determinism, and validation tests
- `sdk/js/` - TypeScript SDK scaffold
- `sdk/python/` - Python SDK scaffold
- `docs/migrations/` - external client migration plans (Godot, Expo, Unreal, Unity)
- `project/` - planning, style, and implementation docs

## Roadmap (Phase 1)

1. Ship core power API for multi-qubit circuit execution (`/v1/circuits/run`) with strict limits.
2. Keep `/v1/gates/run` and `/v1/text/transform` stable for existing consumers.
3. Expand into transpilation and backend discovery in Phase 2.
4. Defer SDK productization to Phase 6.

## License

Apache-2.0.
