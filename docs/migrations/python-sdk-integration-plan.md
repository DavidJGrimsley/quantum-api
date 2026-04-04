# Python SDK Integration Plan

This plan covers the package-ready Python SDK in `sdk/python/`.

The long-term distribution target is PyPI. In the meantime, this repo folder is the source package you install locally or in a virtual environment.

## 1. Intended Consumers

- scripts
- CLIs
- service integrations
- backend-side orchestration or admin tools

## 2. Package Shape

- Source package: `sdk/python/quantum_api_sdk/`
- Build metadata: `sdk/python/pyproject.toml`
- Tests: `tests/test_python_sdk.py`
- Example: `sdk/python/examples/smoke.py`

The SDK normalizes:

- `http://127.0.0.1:8000` -> `http://127.0.0.1:8000/v1`
- `https://<your-domain>/public-facing/api/quantum` -> `https://<your-domain>/public-facing/api/quantum/v1`

## 3. Auth Expectations

- public routes such as `health()` and `portfolio()` default to no auth
- `/keys*` and `/ibm/profiles*` default to bearer auth
- runtime routes default to `X-API-Key`
- each call can override auth mode

## 4. Testing Instructions

### Local package install and syntax check

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e sdk/python pytest
python -m py_compile sdk/python/quantum_api_sdk/*.py tests/test_python_sdk.py
```

What this proves:

- the editable install works
- package metadata is usable
- the SDK imports cleanly
- core modules compile

### Unit verification

```bash
python -m pytest --noconftest tests/test_python_sdk.py -q
```

Current unit coverage validates:

- API-key header injection
- mounted base URL normalization
- bearer-token behavior for `/keys*`
- structured `QuantumApiError` parsing

### Live smoke against a real API

Use a short inline script so you do not have to edit the example file:

```bash
export QUANTUM_API_BASE_URL="http://127.0.0.1:8000"
export QUANTUM_API_KEY="qapi_devlocal_0123456789abcdef0123456789abcdef"

python - <<'EOF'
import os
from quantum_api_sdk import QuantumApiClient

with QuantumApiClient(
    base_url=os.environ["QUANTUM_API_BASE_URL"],
    api_key=os.environ["QUANTUM_API_KEY"],
) as client:
    print(client.health())
    print(client.run_gate({"gate_type": "bit_flip"}))
    print(client.transform_text({"text": "memory and quantum signal"}))
EOF
```

### Consumer-script smoke

After the SDK passes locally:

1. install it into the target virtualenv or service image
2. run `health()`
3. run one protected runtime call
4. intentionally trigger one validation error and confirm the caller surfaces `status_code`, `code`, `request_id`, and `details`

## 5. Expected Test Coverage

- public health call
- protected runtime call with `X-API-Key`
- bearer-auth route
- mounted base URL normalization
- structured API error parsing
