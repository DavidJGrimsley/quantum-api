# Optimization TSP

Use `POST /v1/optimization/tsp` to solve a small symmetric traveling-salesperson problem from a caller-supplied distance matrix.

Set `QUANTUM_API_BASE_URL` and `QUANTUM_API_KEY` before running the example client code.

Example request:

```json
{
  "distance_matrix": [
    [0.0, 10.0, 15.0, 20.0],
    [10.0, 0.0, 35.0, 25.0],
    [15.0, 35.0, 0.0, 30.0],
    [20.0, 25.0, 30.0, 0.0]
  ],
  "solver": "exact",
  "reps": 1,
  "optimizer": {"name": "cobyla", "maxiter": 25},
  "shots": 512,
  "seed": 7
}
```
