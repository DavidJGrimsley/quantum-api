# Optimization VQE

Use `POST /v1/optimization/vqe` to minimize a Pauli-sum Hamiltonian with a real-amplitudes ansatz and a configurable classical optimizer.

Set `QUANTUM_API_BASE_URL` and `QUANTUM_API_KEY` before running the example client code.

Example request:

```json
{
  "pauli_sum": [
    {"pauli": "ZI", "coefficient": 1.0},
    {"pauli": "IZ", "coefficient": -0.5},
    {"pauli": "XX", "coefficient": 0.2}
  ],
  "ansatz": {"type": "real_amplitudes", "reps": 1},
  "optimizer": {"name": "cobyla", "maxiter": 25},
  "shots": 512,
  "seed": 7
}
```
