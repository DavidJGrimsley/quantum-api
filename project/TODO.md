# TODO - Quantum API Phase Checklist

## Phase 1A - Foundation

- [x] Initialize Python project with `pyproject.toml`
- [x] Configure Ruff and Pytest
- [x] Add Dockerfile and `.dockerignore`
- [x] Add `.env.example`
- [x] Add Apache-2.0 license
- [x] Add GitHub Actions CI workflow

## Phase 1B - Backend Core

- [x] Create modular FastAPI structure (`api`, `models`, `services`)
- [x] Implement `/v1/health`
- [x] Implement `/v1/echo-types`
- [x] Implement `/v1/gates/run`
- [x] Implement `/v1/text/transform`
- [x] Add settings-driven request guardrails (length/timeouts)
- [x] Add sanitized global error handling

## Phase 1C - Documentation

- [x] Author root README
- [x] Rewrite `project/info.md`
- [x] Rewrite `project/style.md`
- [x] Rewrite this `project/TODO.md`
- [x] Add canonical plan doc in `project/quantum-api-plan.md`

## Phase 1D - SDK Scaffolds

- [x] Create TypeScript SDK scaffold (`sdk/js`)
- [x] Create Python SDK scaffold (`sdk/python`)
- [x] Add smoke usage examples

## Phase 1E - External Migration Planning

- [x] Create Godot migration plan doc
- [x] Create Expo animation migration plan doc
- [x] Create Unreal Engine integration plan doc
- [x] Create Unity Engine integration plan doc

## Phase 2A - Godot Reusable Addon

- [ ] Create `addons/quantum_api_client/` structure in a Godot-targeted repo
- [ ] Implement `QuantumApiClient.gd` wrapper for `/v1` endpoints
- [ ] Add project-level config for API base URL and timeout
- [ ] Add sample scene/script showing addon integration
- [ ] Add addon README with install + usage

## Phase 2B - Unreal Runtime Client

- [ ] Define Unreal runtime HTTP approach (Blueprint-only wrappers vs C++ plugin)
- [ ] Implement endpoint wrapper methods mirroring `/v1` routes
- [ ] Add Unreal environment config for API base URL
- [ ] Add runtime error/fallback handling patterns
- [ ] Add integration test checklist for packaged build scenarios

## Phase 2C - Unity Runtime Client

- [ ] Define Unity runtime HTTP approach (`UnityWebRequest` + async tasks/coroutines)
- [ ] Implement C# endpoint wrapper methods mirroring `/v1` routes
- [ ] Add Unity environment config for API base URL
- [ ] Add runtime error/fallback handling patterns
- [ ] Add integration test checklist for desktop/mobile builds

## Verification

- [x] Run lint
- [x] Run tests
- [x] Resolve any failures and rerun
