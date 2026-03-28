# Expo Animation Migration Plan

Target upstream app: `text-adventure/`

This plan migrates Expo app API usage to the Quantum API `/v1` contract.

## 1. Endpoint Mapping

| Legacy | New |
|---|---|
| `POST /public-facing/api/quantum/quantum_gate` | `POST /v1/gates/run` |
| `GET /public-facing/api/quantum/health` | `GET /v1/health` |
| `GET /public-facing/api/quantum/quantum_echo_types` | `GET /v1/echo-types` |

## 2. Environment Variable Strategy

Use Expo public env var and a single API helper.

- Add to env files:
  - `EXPO_PUBLIC_QUANTUM_API_BASE_URL=https://<your-domain>/v1`
- Create a helper module (recommended):
  - `src/lib/quantumApi.ts`
- Helper should export:
  - `getQuantumApiBaseUrl()`
  - `postGateRun(payload)`
  - `getHealth()`
  - `getEchoTypes()`

## 3. Request and Response Diffs

### Gate call

Old request:

```json
{
  "gate_type": "rotation",
  "rotation_angle": 1.047
}
```

New request:

```json
{
  "gate_type": "rotation",
  "rotation_angle_rad": 1.047
}
```

New response consumed by animation:

```json
{
  "gate_type": "rotation",
  "measurement": 1,
  "superposition_strength": 0.87,
  "success": false
}
```

## 4. File-by-File Checklist

### `src/components/QuantumAnimation.tsx`

- Replace hardcoded `quantumBaseUrl` with env-driven base URL helper.
- Replace endpoint suffix from `/quantum_gate` to `/gates/run`.
- Rename request key from `rotation_angle` to `rotation_angle_rad`.
- Keep response parsing for:
  - `measurement`
  - `superposition_strength`
  - `success`
- Update explanatory UI text/links to remove legacy path.

### `src/components/ServerLink.tsx`

- Replace static external link with env-driven base URL.
- Ensure displayed text matches configured base URL.

## 5. Suggested Implementation Steps

1. Add env var and helper module.
2. Migrate `QuantumAnimation.tsx` fetch path + payload shape.
3. Migrate `ServerLink.tsx` URL rendering.
4. Run web build and verify animation behavior.
5. Verify error handling in offline/API-down scenario.

## 6. Verification Cases

- Rotation call returns valid payload and drives animation values.
- Non-rotation gate requests still succeed without `rotation_angle_rad`.
- API timeout/network errors trigger fallback animation mode.
- UI shows correct API base URL in links/tooling text.
