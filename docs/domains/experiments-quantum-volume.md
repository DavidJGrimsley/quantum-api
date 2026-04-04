# Quantum Volume

Use `POST /v1/experiments/quantum_volume` to run a small quantum-volume benchmark and report the heavy-output summary from Qiskit Experiments.

Set `QUANTUM_API_BASE_URL` and `QUANTUM_API_KEY` before running the example client code.

Example request:

```json
{
  "qubits": [0, 1],
  "trials": 5,
  "shots": 128,
  "seed": 7
}
```
