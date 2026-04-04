# Quantum API Unreal Plugin

Runtime Unreal Engine plugin scaffold for the Quantum API mounted `/v1` contract.

## Phase 6 scope

This first plugin pass targets the gameplay subset:

- `GET /v1/health`
- `POST /v1/text/transform`
- `POST /v1/gates/run`

Planned follow-on once the base layer is stable:

- `POST /v1/circuits/run`
- `POST /v1/jobs/circuits`
- `GET /v1/jobs/{job_id}`
- `GET /v1/jobs/{job_id}/result`
- `POST /v1/jobs/{job_id}/cancel`

## Auth posture

- Production default: point the plugin at a backend proxy that exposes the same mounted `/v1` contract.
- Direct API-key mode is supported for local/dev/demo/game jam use only.
- The plugin runtime also supports an optional bearer token field for proxy-authenticated requests.

## Layout

- `QuantumApi.uplugin` - plugin descriptor
- `Source/QuantumApi/` - runtime module
- `Config/DefaultQuantumApi.ini` - example settings

## Settings

Configure the mounted base URL, for example:

- Local: `http://127.0.0.1:8000/v1`
- Mounted production: `https://davidjgrimsley.com/public-facing/api/quantum/v1`

The settings object supports:

- base URL normalization
- backend-proxy vs direct-dev auth mode
- optional default `X-API-Key`
- optional default bearer token
- request timeout

## Verification

This repo does not include an Unreal build environment in CI. Treat this plugin as a package-ready scaffold until it has been built and smoke-tested inside a real Unreal project.
