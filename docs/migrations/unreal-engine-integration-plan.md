# Unreal Engine Integration Plan

This plan adds Unreal Engine runtime support for the Quantum API `/v1` contract.

Reference scaffold path in this repo: `sdk/unreal/`

## 1. Key Constraint

- Unreal Python is intended for editor scripting/automation workflows.
- For packaged game runtime API calls, use Unreal runtime HTTP (C++ and/or Blueprint wrappers).

## 2. Endpoint Mapping

Use the same mounted `/v1` contract as other clients. The initial Unreal runtime layer should prioritize the gameplay subset first:

- `GET /v1/health`
- `POST /v1/text/transform`
- `POST /v1/gates/run`
- `GET /v1/echo-types` (secondary metadata call, not required for a minimal first integration)
- Optional follow-on once the base layer is stable:
  - `POST /v1/circuits/run`
  - `POST /v1/jobs/circuits`
  - `GET /v1/jobs/{job_id}`
  - `GET /v1/jobs/{job_id}/result`
  - `POST /v1/jobs/{job_id}/cancel`

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
- Store a mounted `/v1` base URL in project config/settings.
- Avoid hardcoded domains in gameplay scripts/blueprints.

4. Auth posture:
- Default documentation and examples to backend-proxy mode for shipped games.
- Keep direct API-key mode available only for local/dev/demo workflows.

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
2. Add request/response structs for the gameplay subset first.
3. Add Blueprint-callable facade methods.
4. Add timeout/retry/fallback behavior per call type.
5. Add on-screen debug logging for integration phase.
6. Verify both backend-proxy and direct-dev auth modes.
7. Run packaged build smoke tests against staging API.
8. Prepare the plugin for package-ready distribution, but defer public release until after Godot and core SDK validation are green.

## 6. Validation Checklist

- Health endpoint reachable at runtime.
- Gate calls succeed for `bit_flip`, `phase_flip`, and `rotation`.
- Rotation validation errors handled gracefully in UI/game flow.
- Text transform results are parsed and applied safely.
- API-down behavior falls back cleanly without blocking gameplay.
- Backend-proxy mode is the documented production default.
- Direct API-key mode is documented as dev/demo only.

## 7. Testing Instructions

Validate the Unreal plugin in a real Unreal project:

1. Copy `sdk/unreal/` into `<YourProject>/Plugins/QuantumApi/`.
2. Regenerate project files if needed and build the project so the plugin module compiles.
3. Enable the plugin in Unreal if it is not already enabled.
4. Configure the mounted API base URL and auth mode:
   - edit `Config/DefaultQuantumApi.ini`
   - or use the plugin settings UI if exposed in your project build
5. Create a simple Blueprint or C++ harness that calls:
   - `HealthCheck`
   - `RunGate`
   - `TransformText`
6. In Play In Editor, verify:
   - `HealthCheck` returns a healthy response
   - `RunGate` succeeds for `bit_flip`, `phase_flip`, and `rotation`
   - `RunGate` with missing `rotation_angle_rad` triggers the expected error path
   - `TransformText` returns parsed text and category metadata
   - API-down behavior routes into `OnError` without blocking the game thread
7. Package one development build and repeat a minimal smoke test to confirm runtime HTTP behavior outside the editor.

This repo does not include Unreal CI/build automation, so current verification is intentionally manual.
