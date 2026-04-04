# Amplitude Estimation

Use `POST /v1/algorithms/amplitude_estimation` to run one of the supported amplitude-estimation variants against an `EstimationProblem`-style payload.

Set `QUANTUM_API_BASE_URL` and `QUANTUM_API_KEY` before running the example client code.

Example request:

```json
{
  "variant": "ae",
  "state_preparation": {
    "num_qubits": 1,
    "operations": [{"gate": "ry", "target": 0, "theta": 1.2}]
  },
  "objective_qubits": [0],
  "num_eval_qubits": 2,
  "shots": 256,
  "seed": 7
}
```
