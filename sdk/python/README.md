# Quantum API Python SDK

Package-ready sync Python client for the Quantum API `/v1` contract.

This SDK targets scripts, CLIs, service integrations, and backend-side automation. It keeps a sync `httpx` client as the default public surface and supports context-manager usage.

## Current Scope

- Typed core, jobs, and domain methods; use HTTP for QRNG routes
- Mounted base URL normalization:
  - `http://127.0.0.1:8000` -> `http://127.0.0.1:8000/v1`
  - `https://example.com/public-facing/api/quantum` -> `https://example.com/public-facing/api/quantum/v1`
  - `https://example.com/public-facing/api/quantum/v1` stays unchanged
- Auth support for:
  - `X-API-Key` runtime endpoints
  - per-call auth override
- Structured `QuantumApiError`

## Install

```bash
pip install quantum-api-sdk
```

For local development in this repo:

```bash
python3 -m pip install -e sdk/python
```

## Basic Usage

```python
from quantum_api_sdk import QuantumApiClient, QuantumApiError

with QuantumApiClient(
    base_url="http://127.0.0.1:8000",
    api_key="your-runtime-key",
) as client:
    try:
        health = client.health()
        gate = client.run_gate({"gate_type": "rotation", "rotation_angle_rad": 1.57079632679})
        print(health["status"], gate["measurement"])
    except QuantumApiError as exc:
        print(exc.status_code, exc.code, exc.request_id, exc.details)
```

## Auth Modes

The client defaults to `auto` auth mode:

- `health` and `portfolio.json` -> public
- the runtime methods listed below -> API key (unless overridden)

Per-call override examples:

```python
client.health(auth="none")
client.echo_types(auth="api_key")
```

## Runtime credentials

Use an existing API key supplied by the owner or a backend proxy. For IBM jobs, use an existing profile name or the owner's default.

## Production Recommendation

For distributed apps and games, prefer a backend-proxy flow so secrets are not embedded in shipped clients. Direct API-key usage is best kept for local, prototype, demo workflows, or game jams.

## Method Surface

- Core:
  - `health`
  - `portfolio`
  - `echo_types`
  - `run_gate`
  - `run_circuit`
  - `transform_text`
- Runtime:
  - `list_backends`
  - `transpile`
  - `import_qasm`
  - `export_qasm`
  - `run_qasm`
- Jobs:
  - `submit_circuit_job`
  - `submit_qasm_job`
  - `get_circuit_job`
  - `get_circuit_job_result`
  - `cancel_circuit_job`
- Domains:
  - `grover_search`
  - `amplitude_estimation`
  - `phase_estimation`
  - `time_evolution`
  - `qaoa`
  - `vqe`
  - `maxcut`
  - `knapsack`
  - `tsp`
  - `state_tomography`
  - `randomized_benchmarking`
  - `quantum_volume`
  - `t1`
  - `t2_ramsey`
  - `portfolio_optimization`
  - `portfolio_diversification`
  - `kernel_classifier`
  - `vqc_classifier`
  - `qsvr_regressor`
  - `ground_state_energy`
  - `fermionic_mapping_preview`

## Verification

The broader repo environment may not have `uv` or test dependencies installed. If you are validating the SDK locally, install the package first and then run your preferred build/test flow.
