# Optimization QAOA

Use `POST /v1/optimization/qaoa` to solve a normalized binary quadratic program with QAOA over the local statevector sampler path.

Set `QUANTUM_API_BASE_URL` and `QUANTUM_API_KEY` before running the example client code.

Example request:

```json
{
  "problem": {
    "num_variables": 2,
    "linear": [1.0, -2.0],
    "quadratic": [{"i": 0, "j": 1, "value": 2.0}],
    "sense": "minimize"
  },
  "reps": 1,
  "optimizer": {"name": "cobyla", "maxiter": 25},
  "shots": 512,
  "seed": 7
}
```
