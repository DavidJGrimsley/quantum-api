# Expo Animation Migration Plan

Target upstream app: `text-adventure/`

Status: completed for the current `DJsPortfolio-new-api` integration on April 1, 2026. Keep this file as migration/reference guidance.

This plan migrates Expo app API usage to the Quantum API `/v1` contract with API-key auth for protected runtime calls.

## 1. Endpoint Mapping

| Legacy | New |
|---|---|
| `GET /public-facing/api/quantum/portfolio.json` | `GET /v1/portfolio.json` |
| `POST /public-facing/api/quantum/quantum_gate` | `POST /v1/gates/run` |
| `GET /public-facing/api/quantum/health` | `GET /v1/health` |
| `GET /public-facing/api/quantum/quantum_echo_types` | `GET /v1/echo-types` |

## 2. Authentication and Environment Strategy

- Add to env files:
  - `EXPO_PUBLIC_QUANTUM_API_BASE_URL` (default local: `http://127.0.0.1:8000/v1`)
  - `EXPO_PUBLIC_QUANTUM_API_KEY` (low-quota demo key for protected runtime calls)
- Public route behavior:
  - `GET /v1/health` and `GET /v1/portfolio.json` are public.
- Protected route behavior:
  - Runtime endpoints such as `/v1/gates/run`, `/v1/echo-types`, `/v1/text/transform` require `X-API-Key`.

## 3. Shared Helper Module

- Create a helper module:
  - `src/services/quantumApi.ts`
- Helper should export:
  - `getQuantumApiBaseUrl()`
  - `getQuantumPortfolioUrl()`
  - `getQuantumApiKey()`
  - `getQuantumApiHeaders()`
  - `hasQuantumApiKey()`

## 4. Request and Response Diffs

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

### Required headers for protected call

```http
X-API-Key: <your_api_key>
Content-Type: application/json
```

## 5. File-by-File Checklist

### `src/components/QuantumAnimation.tsx`

- Replace hardcoded legacy base URL with helper-driven `/v1` base URL.
- Replace endpoint from `/quantum_gate` to `/gates/run`.
- Rename request key from `rotation_angle` to `rotation_angle_rad`.
- Send `X-API-Key` when available.
- Gracefully fall back to classical mode when API key is missing or invalid.
- Update explanatory UI links/text from legacy path to `/v1`.

### `src/app/(tabs)/public-facing/api/index.tsx`

- Replace portfolio metadata URL with helper-driven `${BASE_URL}/portfolio.json`.
- Keep fallback API card behavior if metadata fetch fails.

### `src/app/(tabs)/public-facing/api/quantum.tsx`

- Replace legacy metadata and endpoint references with `/v1` equivalents.
- Render endpoint auth requirements from metadata.
- Wire endpoint cards to send API key for `api_key` routes.
- Disable noisy live/test calls when required credentials are unavailable.

### `src/components/PublicFacing/api/APIComponents.tsx`

- Accept optional auth label and extra headers.
- Use provided headers for live GET/test requests.
- Show clear guidance when auth is required but credentials are missing.

## 6. Suggested Migration Order

1. Add env vars and helper module.
2. Migrate metadata URL and runtime fetches to `/v1`.
3. Add API key header support and graceful fallback UX.
4. Update code snippets/copy to `/v1` contracts.
5. Validate local flow and web build.

## 7. Verification Cases

- `GET /v1/portfolio.json` returns metadata used by API index/detail pages.
- `POST /v1/gates/run` with valid `X-API-Key` returns `measurement`, `superposition_strength`, `success`.
- Missing/invalid API key on protected calls does not crash the page and shows fallback behavior.
- Rotation call uses `rotation_angle_rad` and succeeds.
- UI displays `/v1` URLs (no legacy `public-facing/api/quantum/*` references).

## 8. Testing Instructions

Use this order so failures are easy to isolate:

1. Verify the shared JS SDK first:
   - `npm --prefix sdk/js install`
   - `npm --prefix sdk/js run check`
   - `npm --prefix sdk/js run build`
   - `npm --prefix sdk/js run test`
2. Point the upstream Expo app at either:
   - local API: `http://127.0.0.1:8000`
   - mounted deployment: `https://<your-domain>/public-facing/api/quantum`
3. Set Expo env vars:
   - `EXPO_PUBLIC_QUANTUM_API_BASE_URL`
   - `EXPO_PUBLIC_QUANTUM_API_KEY`
4. Start the app with the normal Expo dev flow for that project.
5. Run a manual smoke pass:
   - open the API detail/index screens and confirm `portfolio.json` content renders
   - trigger the animation path that calls `POST /v1/gates/run`
   - remove or invalidate the API key and confirm fallback UX still works
   - confirm no UI copy or request logging still references legacy `quantum_gate` or `quantum_echo_types` routes

If you want a quick SDK-only live smoke before touching the Expo app, build `sdk/js/` and run a tiny Node script against `sdk/js/dist/index.js` with a real base URL and key.
