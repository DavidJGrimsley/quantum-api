# Randomized Benchmarking

Use `POST /v1/experiments/randomized_benchmarking` to generate short randomized benchmarking runs on the local Aer simulator and return alpha/EPC fit metrics.

Set `QUANTUM_API_BASE_URL` and `QUANTUM_API_KEY` before running the example client code.

Example request:

```json
{
  "qubits": [0],
  "sequence_lengths": [1, 2, 4, 8],
  "num_samples": 3,
  "shots": 256,
  "seed": 7
}
```
