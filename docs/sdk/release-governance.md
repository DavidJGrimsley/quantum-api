# SDK Release Governance

This document defines how Quantum API client releases work during and after Phase 6.

## Current Phase 6 default

- `sdk/js`, `sdk/python`, `sdk/pennylane`, the Godot addon/client path, the Unreal plugin, and the Unity runtime helper (`sdk/unity/`) should be treated as `package-ready`. The Unity helper awaits in-editor validation and package publishing, but the scaffold and package metadata are in place.
- Public publication is a separate release decision and is not implied by a passing implementation branch.
- Engine clients should default their production guidance to backend-proxy usage.
- Direct `X-API-Key` mode remains supported for local, prototype, and demo workflows only.

## Versioning policy

- The API follows semantic versioning at the product level:
  - patch: backwards-compatible fixes and docs-only corrections
  - minor: backwards-compatible endpoint additions, optional fields, new SDK methods
  - major: breaking request/response/auth changes or removed public behavior
- SDKs and engine clients also follow semantic versioning independently.
- A client minor release may add support for new `/v1` endpoints without requiring an API major release.
- A client major release is required when its public API, auth defaults, packaging contract, or runtime assumptions change incompatibly.

## Changelog policy

- Keep a top-level `CHANGELOG.md` as the release ledger for the API and first-party clients.
- Each entry should call out:
  - API changes
  - JS SDK changes
  - Python SDK changes
  - Godot addon/client changes
  - Unreal plugin changes
  - Unity runtime helper changes
- Mark entries as one of:
  - `Added`
  - `Changed`
  - `Fixed`
  - `Deprecated`
  - `Removed`
  - `Security`

## Compatibility tracking

- Maintain the compatibility matrix in [compatibility-matrix.md](./compatibility-matrix.md).
- Update the matrix whenever:
  - `/v1` gains a new supported endpoint group
  - an SDK/client reaches package-ready status
  - an SDK/client changes auth defaults or runtime support assumptions

## Package-ready checklist

- Package metadata is complete and not marked as internal/private.
- Install/build output is deterministic.
- README usage examples match the current `/v1` contract.
- Auth guidance documents both backend-proxy and direct-dev modes.
- Error handling preserves `error`, `message`, `details`, `request_id`, HTTP status, and headers where available.
- Base URL rules cover both local `/v1` and mounted `/public-facing/api/quantum/v1`.
- The client has smoke coverage for install/build plus contract-level request handling.

## Public publishing checklist

- Package-ready checklist is green.
- Changelog entry is written.
- Compatibility matrix is updated.
- Version bump is intentional and reviewed.
- Distribution credentials/tokens are available.
- External install instructions are verified from a clean environment.
- Godot AssetLib archive output is verified via `git archive --format=tar HEAD | tar -tf -` and contains only `addons/` paths.

## Tooling bootstrap note

The repo should not assume local tooling is preinstalled. Any release or verification instructions must state the expected tools explicitly, including:

- Python toolchain
- `uv` for backend and Python SDK workflows
- Node.js and npm
- TypeScript compiler/runtime requirements for the JS SDK
- Godot and Unreal Engine versions for engine deliverables
