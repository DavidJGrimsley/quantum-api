# State Tomography

Use `POST /v1/experiments/state_tomography` to reconstruct a density matrix for a submitted circuit and optionally compare it against a target statevector.

Set `QUANTUM_API_BASE_URL` and `QUANTUM_API_KEY` before running the example client code.

Example request:

```json
{
  "circuit": {
    "num_qubits": 1,
    "operations": [{"gate": "h", "target": 0}]
  },
  "shots": 512,
  "seed": 7,
  "target_statevector": [
    {"real": 0.70710678, "imag": 0.0},
    {"real": 0.70710678, "imag": 0.0}
  ]
}
```
