# JS SDK Integration Plan

This plan covers the package-ready JavaScript/TypeScript SDK in `sdk/js/`.

The long-term distribution target is npm. In the meantime, this repo folder is the source package you build, test, and consume locally.

## 1. Intended Consumers

- Expo apps
- web apps
- Node services that already use `fetch`
- TypeScript tools and scripts

## 2. Package Shape

- Source: `sdk/js/src/`
- Build output: `sdk/js/dist/`
- Tests: `sdk/js/tests/`
- Example: `sdk/js/examples/smoke.ts`

The SDK normalizes:

- `http://127.0.0.1:8000` -> `http://127.0.0.1:8000/v1`
- `https://<your-domain>/public-facing/api/quantum` -> `https://<your-domain>/public-facing/api/quantum/v1`

## 3. Auth Expectations

- public routes such as `health()` and `portfolio()` do not require auth
- `/keys*` and `/ibm/profiles*` default to bearer auth
- runtime routes default to `X-API-Key`
- every request can override auth mode

## 4. Testing Instructions

### Static and unit verification

Run these from the repo root:

```bash
npm --prefix sdk/js install
npm --prefix sdk/js run check
npm --prefix sdk/js run build
npm --prefix sdk/js run test
```

What these prove:

- TypeScript declarations still line up with the SDK code
- the package can build into `dist/`
- base URL normalization still works
- auth header selection still works
- structured `QuantumApiError` parsing still works

### Live smoke against a real API

1. Choose a target:
   - local: `http://127.0.0.1:8000`
   - mounted deployment: `https://<your-domain>/public-facing/api/quantum`
2. Export env vars:

```bash
export QUANTUM_API_BASE_URL="http://127.0.0.1:8000"
export QUANTUM_API_KEY="qapi_devlocal_0123456789abcdef0123456789abcdef"
```

3. Build the package:

```bash
npm --prefix sdk/js run build
```

4. Run a minimal live smoke:

```bash
node --input-type=module <<'EOF'
import { QuantumApiClient } from "./sdk/js/dist/index.js";

const client = new QuantumApiClient({
  baseUrl: process.env.QUANTUM_API_BASE_URL,
  apiKey: process.env.QUANTUM_API_KEY,
});

console.log(await client.health());
console.log(await client.runGate({ gate_type: "bit_flip" }));
console.log(await client.transformText({ text: "memory and quantum signal" }));
EOF
```

### Consumer-app smoke

After the SDK passes locally:

1. install it into the target app from npm or a local path
2. call `health`, one protected runtime route, and one error-path route
3. confirm the app handles missing/invalid API keys without crashing

## 5. Expected Test Coverage

- public health call
- protected runtime call with `X-API-Key`
- bearer-auth call for `/keys*` or `/ibm/profiles*`
- base URL normalization for mounted deployments
- structured error parsing on `429` or validation errors
