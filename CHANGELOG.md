# Changelog

All notable changes to Quantum API and its first-party clients should be documented in this file.

The format is based on Keep a Changelog and uses semantic versioning expectations described in [docs/sdk/release-governance.md](docs/sdk/release-governance.md).

## Unreleased

### Added

- Phase 6 SDK-first rollout work for package-ready JS/Python clients, Godot migration, and Unreal runtime plugin scaffolding.
- Added `POST /v1/qasm/run` for synchronous OpenQASM execution (finite-shot and analytic statevector mode).
- Added `POST /v1/jobs/qasm` for asynchronous IBM hardware execution from OpenQASM payloads.
- Added Python SDK methods `run_qasm(...)` and `submit_qasm_job(...)`.
- Added `sdk/pennylane` as a package-ready PennyLane plugin (`quantum-api-pennylane`) with `quantum.api` device entry point.
- Added `QuantumApiDevice` finite-shot counts reconstruction and analytic statevector measurement handling through `/v1/qasm/run`.
- Added PennyLane plugin tests and clean-venv artifact smoke validation.

### Changed

- Release governance now distinguishes `package-ready` from public package publishing.
- Added `.gitattributes` export filtering so Godot Asset Library downloads include only `addons/` content.
- Renamed phase-dependent internals to descriptive module names: `models/phase2.py` -> `models/runtime_contracts.py` and `services/phase2_errors.py` -> `services/service_errors.py`; renamed `Phase2ServiceError` to `QuantumApiServiceError`.
- Expanded `.github/workflows/publish-sdk.yml` to include Python SDK and PennyLane package build, validation, and PyPI publish jobs using PyPI Trusted Publisher (OIDC).

