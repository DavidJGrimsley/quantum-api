# Optimization MaxCut

Use `POST /v1/optimization/maxcut` to solve a weighted graph cut problem with either QAOA or the exact eigensolver path.

Set `QUANTUM_API_BASE_URL` and `QUANTUM_API_KEY` before running the example client code.

Example request:

```json
{
  "num_nodes": 3,
  "edges": [
    {"source": 0, "target": 1, "weight": 1.5},
    {"source": 1, "target": 2, "weight": 2.0},
    {"source": 0, "target": 2, "weight": 0.5}
  ],
  "solver": "qaoa",
  "reps": 1,
  "optimizer": {"name": "cobyla", "maxiter": 25},
  "shots": 512,
  "seed": 7
}
```
