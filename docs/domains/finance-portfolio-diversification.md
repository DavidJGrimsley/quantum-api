# Finance Portfolio Diversification

Use `POST /v1/finance/portfolio_diversification` to pick a small set of representative assets from a caller-supplied similarity matrix.

Set `QUANTUM_API_BASE_URL` and `QUANTUM_API_KEY` before running the example client code.

Example request:

```json
{
  "similarity_matrix": [
    [1.0, 0.2, 0.3],
    [0.2, 1.0, 0.4],
    [0.3, 0.4, 1.0]
  ],
  "num_clusters": 2,
  "asset_labels": ["ALPHA", "BETA", "GAMMA"],
  "solver": "exact",
  "optimizer": {"name": "cobyla", "maxiter": 25},
  "reps": 1,
  "shots": 512,
  "seed": 7
}
```
