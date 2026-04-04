# T1 Experiment

Use `POST /v1/experiments/t1` to run a small T1 relaxation experiment for a single qubit and return the fitted decay constant.

Set `QUANTUM_API_BASE_URL` and `QUANTUM_API_KEY` before running the example client code.

Example request:

```json
{
  "qubits": [0],
  "delays": [0.000001, 0.000002, 0.000003, 0.000004],
  "shots": 128,
  "seed": 7
}
```
