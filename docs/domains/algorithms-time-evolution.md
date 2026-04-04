# Time Evolution

Use `POST /v1/algorithms/time_evolution` to evolve a Pauli-sum Hamiltonian with either Trotterized or variational real-time methods.

Set `QUANTUM_API_BASE_URL` and `QUANTUM_API_KEY` before running the example client code.

Example request:

```json
{
  "variant": "trotter_qrte",
  "hamiltonian": [{"pauli": "Z", "coefficient": 1.0}],
  "time": 0.5,
  "initial_state": {
    "num_qubits": 1,
    "operations": [{"gate": "h", "target": 0}]
  },
  "num_timesteps": 2,
  "shots": 256,
  "seed": 7
}
```
