# Phase Estimation

Use `POST /v1/algorithms/phase_estimation` to run standard, iterative, or Hamiltonian phase-estimation workflows with the API's supported circuit and Pauli-sum representations.

Set `QUANTUM_API_BASE_URL` and `QUANTUM_API_KEY` before running the example client code.

Example request:

```json
{
  "variant": "standard",
  "unitary": {
    "num_qubits": 1,
    "operations": [{"gate": "z", "target": 0}]
  },
  "state_preparation": {
    "num_qubits": 1,
    "operations": [{"gate": "h", "target": 0}]
  },
  "num_evaluation_qubits": 3,
  "shots": 256,
  "seed": 7
}
```
