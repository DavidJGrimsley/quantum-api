# Optimization Knapsack

Use `POST /v1/optimization/knapsack` to choose the highest-value subset of items that still fits within a weight capacity.

Set `QUANTUM_API_BASE_URL` and `QUANTUM_API_KEY` before running the example client code.

Example request:

```json
{
  "item_values": [3, 4, 5],
  "item_weights": [2, 3, 4],
  "capacity": 5,
  "solver": "exact",
  "reps": 1,
  "optimizer": {"name": "cobyla", "maxiter": 25},
  "shots": 512,
  "seed": 7
}
```
