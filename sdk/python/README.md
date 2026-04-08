# Quantum API Python SDK

Package-ready sync Python client for the Quantum API `/v1` contract.

This SDK targets scripts, CLIs, service integrations, and backend-side automation. It keeps a sync `httpx` client as the default public surface and supports context-manager usage.

## Current Scope

- Full current `/v1` method surface
- Mounted base URL normalization:
  - `http://127.0.0.1:8000` -> `http://127.0.0.1:8000/v1`
  - `https://example.com/public-facing/api/quantum` -> `https://example.com/public-facing/api/quantum/v1`
  - `https://example.com/public-facing/api/quantum/v1` stays unchanged
- Auth support for:
  - `X-API-Key` runtime endpoints
  - bearer-token `/keys*` and `/ibm/profiles*` flows
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
    bearer_token="your-supabase-jwt",
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
- `/keys*` and `/ibm/profiles*` -> bearer token
- all other `/v1` routes -> API key

Per-call override examples:

```python
client.health(auth="none")
client.echo_types(auth="api_key")
client.list_keys(auth="bearer")
```

## Account Setup (Public Identerest Sign-In)

If you are using the hosted Quantum API account flow (not self-hosting), credentials come from signing in at `https://davidjgrimsley.com/public-facing/api/quantum`.

1. Open `https://davidjgrimsley.com/public-facing/api/quantum` and sign in with an Identerest account.
2. In the `Api Keys` panel, create a Quantum API key and copy it immediately (raw key is shown once).
3. In the `IBM Credentials` panel, create an IBM profile (`profile_name`, IBM API token, IBM instance/CRN, channel), then verify it.
4. Optionally set one IBM profile as default on that same public page.

How those values map into the SDK:

- bearer token from that Identerest-backed sign-in session -> `bearer_token` (used for `/keys*` and `/ibm/profiles*`).
- created Quantum API key -> `api_key` (used for protected runtime `/v1` routes).
- selected IBM profile name -> `ibm_profile` in IBM backend/transpile/job requests.

## IBM Profiles (Per-User IBM Credentials)

This is the flow behind profile cards/actions like Verify, Set Default, Edit, and Delete.

The Python SDK exposes full profile lifecycle methods:

- `list_ibm_profiles()`
- `create_ibm_profile(payload)`
- `update_ibm_profile(profile_id, payload)`
- `verify_ibm_profile(profile_id)`
- `delete_ibm_profile(profile_id)`

Profile routes use bearer auth, so pass the bearer token issued after signing in at `https://davidjgrimsley.com/public-facing/api/quantum` with Identerest.

```python
from quantum_api_sdk import QuantumApiClient

with QuantumApiClient(
  base_url="https://davidjgrimsley.com/public-facing/api/quantum",
  bearer_token=user_access_token,
) as client:
  created = client.create_ibm_profile(
    {
      "profile_name": "Echo Text Adventure Godot Game",
      "token": "your-ibm-token",
      "instance": "crn:v1:bluemix:public:quantum-computing:us-east:a/1234567890abcdef::",
      "channel": "ibm_quantum_platform",
      "is_default": True,
    }
  )

  verify_result = client.verify_ibm_profile(created["profile_id"])
  profiles = client.list_ibm_profiles()

  client.update_ibm_profile(
    created["profile_id"],
    {
      "profile_name": "Echo Text Adventure Godot Game (Prod)",
      "is_default": True,
    },
  )

  # Later, if needed:
  # client.delete_ibm_profile(created["profile_id"])
```

When you submit IBM jobs, pass `ibm_profile` as the selected saved profile name.
If omitted, the backend can use the default profile.

```python
job = client.submit_circuit_job(
  {
    "provider": "ibm",
    "backend_name": "ibm_brisbane",
    "ibm_profile": created["profile_name"],
    "circuit": {
      "qubits": 1,
      "operations": [{"gate": "h", "target": 0}],
    },
    "shots": 1024,
  }
)
```

For shipped production clients, keep IBM tokens server-side and run profile create/update/delete through your backend proxy.

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
- Auth:
  - `list_keys`
  - `create_key`
  - `revoke_key`
  - `rotate_key`
  - `delete_revoked_keys`
  - `delete_key`
  - `list_ibm_profiles`
  - `create_ibm_profile`
  - `update_ibm_profile`
  - `delete_ibm_profile`
  - `verify_ibm_profile`
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
