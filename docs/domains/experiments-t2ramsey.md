# T2 Ramsey Experiment

Use `POST /v1/experiments/t2ramsey` to run a small Ramsey coherence experiment for a single qubit and return the fitted `T2*` result.

Set `QUANTUM_API_BASE_URL` and `QUANTUM_API_KEY` before running the example client code.

Example request:

```json
{
  "qubits": [0],
  "delays": [0.000001, 0.000002, 0.000003, 0.000004, 0.000005],
  "osc_freq": 100000.0,
  "shots": 128,
  "seed": 7
}
```
