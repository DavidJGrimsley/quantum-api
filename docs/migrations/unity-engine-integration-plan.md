# Unity Engine Integration Plan

This plan adds Unity runtime support for the Quantum API `/v1` contract.

## 1. Runtime Approach

- Use `UnityWebRequest` for API communication in runtime gameplay.
- Build a reusable C# client wrapper (`QuantumApiClient`) to centralize URLs, payloads, and error handling.
- Prefer async task wrappers (or coroutines) so gameplay flow remains responsive.

## 2. Endpoint Mapping

Use the same contract as all other clients:

- `GET /v1/health`
- `GET /v1/echo-types`
- `POST /v1/gates/run`
- `POST /v1/text/transform`

## 3. Suggested Unity Client Design

Create a small client layer:

- `Task<HealthResponse> HealthCheckAsync()`
- `Task<EchoTypesResponse> GetEchoTypesAsync()`
- `Task<GateRunResponse> RunGateAsync(GateRunRequest request)`
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

## 6. Validation Checklist

- Health endpoint reachable at runtime.
- Gate calls succeed for all supported gate types.
- Rotation validation errors handled gracefully in gameplay.
- Text transform responses parse correctly.
- API-down mode falls back without freezing gameplay.
