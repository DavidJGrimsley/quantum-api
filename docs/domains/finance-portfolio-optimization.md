# Finance Portfolio Optimization

Use `POST /v1/finance/portfolio_optimization` with caller-supplied expected returns and covariance data. Phase 5 intentionally does not fetch live market data.

Set `QUANTUM_API_BASE_URL` and `QUANTUM_API_KEY` before running the example client code.

Example request:

```json
{
  "expected_returns": [0.1, 0.2, 0.12],
  "covariance_matrix": [
    [0.05, 0.01, 0.02],
    [0.01, 0.06, 0.01],
    [0.02, 0.01, 0.04]
  ],
  "budget": 2,
  "risk_factor": 0.5,
  "solver": "qaoa",
  "optimizer": {"name": "cobyla", "maxiter": 25},
  "reps": 1,
  "shots": 512,
  "seed": 7
}
```
