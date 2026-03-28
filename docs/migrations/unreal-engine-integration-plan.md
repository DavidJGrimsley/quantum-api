# Unreal Engine Integration Plan

This plan adds Unreal Engine runtime support for the Quantum API `/v1` contract.

## 1. Key Constraint

- Unreal Python is intended for editor scripting/automation workflows.
- For packaged game runtime API calls, use Unreal runtime HTTP (C++ and/or Blueprint wrappers).

## 2. Endpoint Mapping

Use the same contract as other clients:

- `GET /v1/health`
- `GET /v1/echo-types`
- `POST /v1/gates/run`
- `POST /v1/text/transform`

## 3. Recommended Unreal Architecture

1. Create a runtime client wrapper layer (`QuantumApiClient`):
- Centralizes base URL, headers, serialization, and retries.
- Exposes strongly named methods:
  - `HealthCheck`
  - `GetEchoTypes`
  - `RunGate`
  - `TransformText`

2. Wrap for gameplay usage:
- C++ implementation using Unreal HTTP module.
- Blueprint-callable functions/events for designers.

3. Config-driven environment:
- Store base URL in project config/settings.
- Avoid hardcoded domains in gameplay scripts/blueprints.

## 4. Payload and Response Contracts

### `RunGate` request

```json
{
  "gate_type": "rotation",
  "rotation_angle_rad": 1.047
}
```

### `RunGate` response

```json
{
  "gate_type": "rotation",
  "measurement": 1,
  "superposition_strength": 0.87,
  "success": false
}
```

### `TransformText` request

```json
{
  "text": "memory signal and quantum circuit"
}
```

### `TransformText` response

```json
{
  "original": "memory signal and quantum circuit",
  "transformed": "...",
  "coverage_percent": 80.0,
  "quantum_words": 4,
  "total_words": 5,
  "category_counts": {}
}
```

## 5. Implementation Steps

1. Build base HTTP client wrapper.
2. Add request/response structs for all endpoints.
3. Add Blueprint-callable facade methods.
4. Add timeout/retry/fallback behavior per call type.
5. Add on-screen debug logging for integration phase.
6. Run packaged build smoke tests against staging API.

## 6. Validation Checklist

- Health endpoint reachable at runtime.
- Gate calls succeed for `bit_flip`, `phase_flip`, and `rotation`.
- Rotation validation errors handled gracefully in UI/game flow.
- Text transform results are parsed and applied safely.
- API-down behavior falls back cleanly without blocking gameplay.
