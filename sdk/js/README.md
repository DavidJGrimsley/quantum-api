# Quantum API JS SDK

Package-ready TypeScript client for the Quantum API `/v1` contract.

This SDK is designed to be the primary frontend-friendly client for browser, Expo, and other TypeScript apps that already use `fetch`.
The default runtime fetch is browser-safe: it binds `window.fetch` in browser-like environments and falls back to `globalThis.fetch` in other runtimes. You can still override this with `fetchImpl` when needed.

## Current Scope

- Full current `/v1` method surface
- Mounted base URL normalization:
  - `http://127.0.0.1:8000` -> `http://127.0.0.1:8000/v1`
  - `https://DavidJGrimsley.com/public-facing/api/quantum` -> `https://DavidJGrimsley.com/public-facing/api/quantum/v1`
  - `https://DavidJGrimsley.com/public-facing/api/quantum/v1` stays unchanged
- Auth support for:
  - `X-API-Key` runtime endpoints
  - bearer-token `/keys*` and `/ibm/profiles*` flows
  - per-request auth override
- Structured `QuantumApiError` with normalized error data and response headers
- Browser-safe default fetch binding with `fetchImpl` override support

## Install

```bash
npm install @mr.dj2u/quantum-api
```

For local development in this repo:

```bash
npm --prefix sdk/js install
npm --prefix sdk/js run build
```

## Basic Usage

```ts
import { QuantumApiClient } from "@mr.dj2u/quantum-api";

const client = new QuantumApiClient({
  baseUrl: process.env.EXPO_PUBLIC_QUANTUM_API_BASE_URL ?? "http://127.0.0.1:8000",
  apiKey: process.env.EXPO_PUBLIC_QUANTUM_API_KEY,
  bearerToken: process.env.EXPO_PUBLIC_SUPABASE_JWT,
});

const health = await client.health();
const gate = await client.runGate({
  gate_type: "rotation",
  rotation_angle_rad: Math.PI / 2,
});
```

Use direct `apiKey` client configuration for local development, prototypes, and trusted internal tooling. For shipped production clients, keep API keys server-side and call a server proxy.

## Auth Modes

The client defaults to `auto` auth mode:

- `health` and `portfolio.json` -> public
- `/keys*` and `/ibm/profiles*` -> bearer token (you don't need these, they are just how you're able to sign in and get keys and store ibm accounts)
- all other `/v1` routes -> API key

You can override auth per request:

```ts
await client.health({ auth: "none" });
await client.echoTypes({ auth: "apiKey" });
await client.listKeys({ auth: "bearer" });
```

## Expo Example

```ts
import { QuantumApiClient, QuantumApiError } from "@mr.dj2u/quantum-api";

const quantum = new QuantumApiClient({
  baseUrl: process.env.EXPO_PUBLIC_QUANTUM_API_BASE_URL ?? "https://example.com/public-facing/api/quantum",
  apiKey: process.env.EXPO_PUBLIC_QUANTUM_API_KEY,
});

try {
  const transformed = await quantum.transformText({ text: "memory and quantum signal" });
  console.log(transformed.transformed);
} catch (error) {
  if (error instanceof QuantumApiError) {
    console.error(error.status, error.code, error.requestId, error.details);
  }
}
```

## Production Recommendation

For shipped game or app clients, use a backend-proxy pattern so long-lived API keys are never embedded in distributable builds.

- Client app authenticates users and calls your backend.
- Your backend injects `X-API-Key` for runtime routes and enforces your own quota/abuse controls.
- Bearer-token flows (`/keys*`, `/ibm/profiles*`) stay server-mediated for key lifecycle and profile management.

Direct API-key mode is best kept for local development, prototypes, demos, or game jams.

## Method Surface

- Core:
  - `health`
  - `portfolio`
  - `echoTypes`
  - `runGate`
  - `runCircuit`
  - `transformText`
- Runtime:
  - `listBackends`
  - `transpile`
  - `importQasm`
  - `exportQasm`
- Auth:
  - `listKeys`
  - `createKey`
  - `revokeKey`
  - `rotateKey`
  - `deleteRevokedKeys`
  - `deleteKey`
  - `listIbmProfiles`
  - `createIbmProfile`
  - `updateIbmProfile`
  - `deleteIbmProfile`
  - `verifyIbmProfile`
- Jobs:
  - `submitCircuitJob`
  - `getCircuitJob`
  - `getCircuitJobResult`
  - `cancelCircuitJob`
- Domains:
  - `groverSearch`
  - `amplitudeEstimation`
  - `phaseEstimation`
  - `timeEvolution`
  - `qaoa`
  - `vqe`
  - `maxcut`
  - `knapsack`
  - `tsp`
  - `stateTomography`
  - `randomizedBenchmarking`
  - `quantumVolume`
  - `t1`
  - `t2Ramsey`
  - `portfolioOptimization`
  - `portfolioDiversification`
  - `kernelClassifier`
  - `vqcClassifier`
  - `qsvrRegressor`
  - `groundStateEnergy`
  - `fermionicMappingPreview`

## Verification

The repo environment may not have `tsc` installed globally. Use the local dev dependency:

```bash
npm --prefix sdk/js install
npm --prefix sdk/js run check
npm --prefix sdk/js run build
npm --prefix sdk/js run test
```

## npm Release Flow

1. Bump `version` in `sdk/js/package.json` (semantic versioning).
2. Ensure dependencies are current (`npm --prefix sdk/js install`).
3. Run local gates:

```bash
npm --prefix sdk/js run check
npm --prefix sdk/js run build
npm --prefix sdk/js run test
npm --prefix sdk/js run pack:dry-run
```

4. Publish with GitHub Actions using `.github/workflows/publish-sdk.yml`:
  - run manually with `workflow_dispatch`, or
  - push a tag like `sdk-v0.1.2`.
5. Ensure repository secret `NPM_TOKEN` exists with publish access for `@mr.dj2u/quantum-api`.
