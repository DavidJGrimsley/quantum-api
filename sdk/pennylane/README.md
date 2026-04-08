# Quantum API PennyLane Plugin

Package-ready PennyLane device plugin for executing circuits through Quantum API `/v1/qasm/run`.

## Install

```bash
pip install quantum-api-pennylane
```

For local development in this repo:

```bash
python3 -m pip install -e sdk/pennylane
```

## Usage

```python
import pennylane as qml

# The plugin is registered under the "quantum.api" PennyLane device name.
dev = qml.device(
    "quantum.api",
    wires=2,
    shots=1000,
    base_url="https://davidjgrimsley.com/public-facing/api/quantum",
    api_key="your-runtime-api-key",
)

@qml.qnode(dev)
def bell():
    qml.Hadamard(0)
    qml.CNOT([0, 1])
    return qml.counts(wires=[0, 1])

print(bell())
```

## Configuration

Constructor keyword arguments:

- `base_url`: Quantum API base URL (with or without `/v1`)
- `api_key`: runtime `X-API-Key` for protected routes
- `bearer_token`: optional bearer token for advanced auth routing
- `timeout`: client timeout in seconds
- `qasm_version`: currently `"auto"`, `"2"`, or `"3"` (default `"auto"`)
- `seed`: optional simulator seed forwarded to `/v1/qasm/run`
- `client`: optional preconfigured `quantum_api_sdk.QuantumApiClient`

Finite-shot QNodes are reconstructed from counts. Analytic QNodes (`shots=None`) use statevector post-processing.
