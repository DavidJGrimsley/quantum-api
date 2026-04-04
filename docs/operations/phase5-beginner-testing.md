# Phase 5 Beginner Testing Guide

This guide is for the live VPS deployment.

If you are feeling lost, the short version is:

- The new endpoints are real and live.
- The easiest safe place to test them is the API docs page.
- You do not need to use notebooks.
- If a page on the website is still calling `https://davidjgrimsley.com/v1/...`, that is the wrong URL.

## The Live URLs

- API docs:
  - `https://davidjgrimsley.com/public-facing/api/quantum/docs`
- Endpoint list:
  - `https://davidjgrimsley.com/public-facing/api/quantum/v1/portfolio.json`
- Health check:
  - `https://davidjgrimsley.com/public-facing/api/quantum/v1/health`

Protected calls use the header:

```http
X-API-Key: <your_quantum_api_key>
```

## What The New Endpoints Mean

- `POST /v1/optimization/qaoa`
  - Solve a small yes-or-no optimization puzzle.
- `POST /v1/optimization/vqe`
  - Estimate a low-energy answer for a math or physics problem.
- `POST /v1/experiments/state_tomography`
  - Reconstruct the state made by a circuit.
- `POST /v1/experiments/randomized_benchmarking`
  - Measure how noisy a small quantum process is.
- `POST /v1/finance/portfolio_optimization`
  - Pick investments given returns, risk, and a budget.
- `POST /v1/ml/kernel_classifier`
  - Train a tiny quantum-flavored classifier and make predictions.
- `POST /v1/nature/ground_state_energy`
  - Estimate the ground-state energy of a very small molecule.

## The Easiest Way To Test

1. Open the health URL in your browser.
   Success looks like JSON with `"status": "healthy"`.
2. Open `portfolio.json`.
   Search for the new Phase 5 endpoints.
3. Open the docs page.
4. Pick one endpoint, click `Try it out`, paste a sample request, and run it.
5. If you get a `200` response, that endpoint is working.

## Sample Body To Try First

Start with `POST /v1/optimization/qaoa`.

```json
{
  "problem": {
    "num_variables": 2,
    "linear": [1.0, -2.0],
    "quadratic": [{"i": 0, "j": 1, "value": 2.0}],
    "sense": "minimize"
  },
  "reps": 1,
  "optimizer": {"name": "cobyla", "maxiter": 5},
  "shots": 128,
  "seed": 7
}
```

Success looks like a `200` response that includes `best_bitstring`.

## Curl Example

```bash
BASE="https://davidjgrimsley.com/public-facing/api/quantum/v1"
API_KEY="YOUR_REAL_KEY"

curl -X POST "$BASE/ml/kernel_classifier" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "training_features": [[0.0,0.0],[0.0,1.0],[1.0,0.0],[1.0,1.0]],
    "training_labels": [0,1,1,0],
    "prediction_features": [[0.1,0.2],[0.9,0.8]],
    "feature_map": {"type":"zz_feature_map","reps":1,"entanglement":"full"},
    "seed": 7
  }'
```

## How To Read Errors

- `200`
  - It worked.
- `401`
  - Missing or invalid API key.
- `404` with website HTML
  - Wrong URL. You hit the website, not the API.
- `422`
  - The JSON body shape is wrong.
- `503 provider_unavailable`
  - The server is missing an optional Qiskit package for that feature.

## Why The Portfolio Page Was Breaking

The API itself was fine. The problem was the URL the page was using for live calls.

- Correct mounted API path example:
  - `/public-facing/api/quantum/v1/optimization/qaoa`
- Broken path example:
  - `/v1/optimization/qaoa`

`/v1/portfolio.json` now emits request-ready endpoint paths when the API is mounted behind `/public-facing/api/quantum`, so simple frontend consumers can use the returned `path` directly.
