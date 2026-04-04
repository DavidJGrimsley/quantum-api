# Godot Game Migration Plan

Target upstream app: `choose-your-own-quantum-adventure-(4.4)/`

This plan migrates game-side API usage from legacy endpoints to the new Quantum API `/v1` contract.

## 1. Endpoint Mapping

| Legacy | New | Notes |
|---|---|---|
| `GET /public-facing/api/quantum/health` or mixed `/api/quantum/health` | `GET /v1/health` | Single canonical health route |
| `GET /public-facing/api/quantum/quantum_echo_types` | `GET /v1/echo-types` | Response format changed |
| `POST /public-facing/api/quantum/quantum_gate` | `POST /v1/gates/run` | Uses `rotation_angle_rad` in radians |
| `POST /public-facing/api/quantum/quantum_text` | `POST /v1/text/transform` | Response always includes `category_counts` |

## 2. Payload and Response Diffs

### Gate execution

Old request:

```json
{
  "gate_type": "rotation",
  "rotation_angle": 0.5
}
```

New request:

```json
{
  "gate_type": "rotation",
  "rotation_angle_rad": 0.5
}
```

New response:

```json
{
  "gate_type": "rotation",
  "measurement": 1,
  "superposition_strength": 0.87,
  "success": false
}
```

### Text transform

Old response could vary by code path.

New response is stable:

```json
{
  "original": "...",
  "transformed": "...",
  "coverage_percent": 70.0,
  "quantum_words": 7,
  "total_words": 10,
  "category_counts": {"scramble": 1, "reverse": 2, "ghost": 1, "quantum_caps": 1, "quantum_gates": 1, "quantum_entanglement": 1, "quantum_interference": 0, "original": 3}
}
```

## 3. Base URL Strategy (Godot)

Create a single source for base URL in the game codebase.

Recommended implementation:

- introduce a shared runtime client at `addons/quantum_api_client/quantum_api_client.gd`
- keep the promoted reusable copy in this repo at `sdk/godot/addons/quantum_api_client/`
- let that client normalize both:
  - `https://<your-domain>/public-facing/api/quantum`
  - `https://<your-domain>/public-facing/api/quantum/v1`
- support both:
  - backend-proxy mode for shipped builds
  - optional direct `X-API-Key` mode for local/dev/demo workflows

Recommended convention:

- `const QUANTUM_API_BASE = "https://<your-domain>/v1"`
- Build endpoint URLs as `QUANTUM_API_BASE + "/gates/run"`, etc.
- Remove direct references to:
  - `DavidJGrimsley.com/public-facing/api/quantum`
  - `DavidJGrimsley.com/api/quantum/...`
  - raw IP URLs like `108.175.12.95:8000`

## 4. File-by-File Checklist

### `source/dialogue/dialogue.gd`

- Replace hardcoded `quantum_gate` URL with `/v1/gates/run`.
- Rename request field `rotation_angle` to `rotation_angle_rad`.
- Keep gate types limited to `bit_flip`, `phase_flip`, `rotation`.
- Ensure fallback behavior still triggers on non-200 responses.

### `source/dialogue/quantum_echo_service.gd`

- Change base URL constant to `/v1` base.
- Update text request target to `/text/transform`.
- Update health target to `/health`.
- Update echo type listing target to `/echo-types` where applicable.
- Ensure transformed text reads from `transformed` only.

### `source/dialogue/QuantumEchoManager.gd`

- Replace `/quantum_text` calls with `/text/transform`.
- Replace `/health` call path to `/v1/health` based on base URL strategy.
- Update any response assumptions to include new schema fields.

### `source/dialogue/dialogue_ui_manager.gd`

- Replace hardcoded text endpoint with `/v1/text/transform`.
- Remove duplicate display calls if present after response handling.
- Ensure request callback selection does not depend on node-group quirks.

### `source/dialogue/quantum_gate_manager.gd`

- Move endpoint from old `/quantum_gate` or `/quantum_gates` usage to `/v1/gates/run`.
- Remove unsupported request fields like `gate_sequence` for the new API.
- Keep internal story logic separate from transport response parsing.

### `source/dialogue/quantum_dialogue_test.gd`

- Update test endpoints to `/v1/gates/run`.
- Change payload shape to new gate contract.
- Assert `measurement`, `success`, and `superposition_strength` instead of legacy fields.

## 5. Suggested Migration Order

1. Introduce the shared Godot Quantum API client/addon.
2. Centralize base URL and auth mode handling there.
3. Migrate gate endpoint callers.
4. Migrate text transform callers.
5. Migrate health and echo-types calls.
6. Update test scripts.
7. Run end-to-end dialogue path checks.

## 6. Validation Scenarios

- Gate success path for each gate type.
- Rotation validation failure (missing `rotation_angle_rad`).
- Text transform with mixed-category sentence.
- Service-down fallback behavior.
- Long text rejection behavior from API.
