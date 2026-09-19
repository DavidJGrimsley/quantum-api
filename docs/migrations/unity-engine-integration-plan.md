# Unity Engine Integration Plan

This plan adds Unity runtime support for the Quantum API `/v1` contract.

The initial package-style scaffold now lives in `sdk/unity/`.

## 1. Runtime Approach

- Use `UnityWebRequest` for API communication in runtime gameplay.
- Build a reusable C# client wrapper (`QuantumApiClient`) to centralize URLs, payloads, and error handling.
- Prefer async task wrappers (or coroutines) so gameplay flow remains responsive.

## 2. Endpoint Mapping

Use the same contract as all other clients:

- `GET /v1/health`
- `GET /v1/echo-types`
- `POST /v1/gates/run`
- `POST /v1/random`
- `POST /v1/text/transform`

## 3. Suggested Unity Client Design

Create a small client layer:

- `Task<HealthResponse> HealthAsync()`
- `Task<EchoTypesResponse> GetEchoTypesAsync()`
- `Task<GateRunResponse> RunGateAsync(GateRunRequest request)`
- `Task<RandomIntResponse> RandomIntAsync(int min, int max)`
- `Task<TextTransformResponse> TransformTextAsync(TextTransformRequest request)`

Keep URL and timeout in config:

- ScriptableObject config, environment loader, or build-time constants.
- Avoid hardcoding endpoint URLs in gameplay scripts.

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

### `RandomInt` request

```json
{
  "min": 0,
  "max": 1
}
```

### `RandomInt` response

```json
{
  "value": 1,
  "source": "qiskit-simulator"
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

1. Build `QuantumApiClient` runtime wrapper.
2. Add DTOs for requests/responses.
3. Add retry/timeout policy with gameplay-safe fallback.
4. Add adapter layer for systems that consume transformed text/quantum gates.
5. Run playmode and build smoke tests.

Current status:

- `sdk/unity/` now contains the initial `UnityWebRequest` client scaffold.
- `sdk/unity/` exposes `RandomIntAsync(0, 1)` and a matching coroutine wrapper for the QRNG endpoint.
- Local Unity editor/package validation completed in a disposable Unity project.

## 6. Validation Checklist

- Health endpoint reachable at runtime.
- Gate calls succeed for all supported gate types.
- `RandomIntAsync(0, 1)` returns bounded `0` or `1` values over repeated calls.
- Rotation validation errors handled gracefully in gameplay.
- Malformed QRNG requests return a readable `QuantumApiError`.
- Text transform responses parse correctly.
- API-down mode falls back without freezing gameplay.

## 7. Testing Instructions

Use a real Unity editor project for validation:

1. Copy `sdk/unity/` into the Unity project's `Packages/` folder, or add it by local path in Package Manager.
2. Confirm the package imports cleanly and the `QuantumApi.Unity` assembly appears without compile errors.
3. Create a simple test scene:
   - add an empty `GameObject`
   - attach a MonoBehaviour that creates `QuantumApiClient`
   - or start from `sdk/unity/Samples~/BasicUsage/QuantumApiExample.cs`
4. Configure:
   - `BaseUrl = http://127.0.0.1:8000` for local beginner validation
   - `BackendProxyMode = false` for local direct-key validation
   - `ApiKey = qapi_devlocal_0123456789abcdef0123456789abcdef`, the documented local dev key
5. Run Play Mode checks:
   - `HealthAsync()` succeeds
   - `GetEchoTypesAsync()` succeeds when auth is configured correctly
   - `RunGateAsync()` succeeds for `bit_flip`, `phase_flip`, and `rotation`
   - `RunGateAsync()` with `gate_type = "rotation"` and no angle yields a clean API error
   - `RandomIntAsync(0, 1)` returns `0` or `1` across repeated calls
   - `RandomIntAsync(1, 0)` yields a clean API validation error
   - `TransformTextAsync()` parses `transformed`, `coverage_percent`, and `category_counts`
   - `TransformTextWithFallbackAsync()` returns fallback text when the API is down
6. Build one standalone player and repeat at least `health` plus one protected call so runtime networking matches Editor behavior.

## 8. Validation Evidence

Validated locally on 2026-09-16 after rebasing `feature/phase-6-5-unity-plugin-trials` onto `origin/main` at `c719af1`.

- Backend focused checks passed: `uv run pytest tests/test_random_api.py tests/test_api_contract.py` (`90 passed`).
- Unity editor used: `C:\Program Files\Unity\Hub\Editor\6000.6.1f1\Editor\Unity.exe`.
- Scratch project used: `D:\SoftwareDev\APIs\quantum-api-i2Workspace\temp\unity-plugin-trials-smoke`.
- Package import used local Package Manager path: `D:\SoftwareDev\APIs\quantum-api-i2Workspace\quantum-api-unity-plugin-trials\sdk\unity`.
- Local API used `http://127.0.0.1:8000`, `BackendProxyMode = false`, and the documented local dev key only.
- Editor smoke log: `D:\SoftwareDev\APIs\quantum-api-i2Workspace\temp\unity-plugin-trials-smoke\Logs\QuantumApiUnitySmoke2.log`.
  - Package compiled without assembly errors.
  - Health returned `healthy` with `qiskit` runtime mode.
  - Echo types returned 8 entries.
  - `bit_flip`, `phase_flip`, and `rotation` gate calls succeeded.
  - Five `RandomIntAsync(0, 1)` calls returned bounded values from `qiskit-simulator`.
  - `RandomIntAsync(1, 0)` returned the expected readable `validation_error`.
  - Text transform succeeded.
  - API-down health check returned the expected readable `request_failed` path.
  - Windows development player built at `Builds/QuantumApiSmoke/QuantumApiSmoke.exe`.
- Standalone player smoke log: `D:\SoftwareDev\APIs\quantum-api-i2Workspace\temp\unity-plugin-trials-smoke\Logs\QuantumApiStandaloneSmoke.log`.
  - Player emitted `[QuantumApiStandaloneSmoke] PASS health=healthy random=1 source=qiskit-simulator`.

Unity CLI was not installed on `PATH`; validation used the installed Unity Editor executable directly. The scratch project, generated player, logs, local database, and Unity-generated artifacts are validation evidence only and should not be committed.
