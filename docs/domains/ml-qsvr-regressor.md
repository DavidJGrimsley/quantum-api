# Machine Learning QSVR Regressor

Use `POST /v1/ml/qsvr_regressor` to fit a quantum-kernel support-vector regressor on caller-supplied training rows and numeric targets.

Set `QUANTUM_API_BASE_URL` and `QUANTUM_API_KEY` before running the example client code.

Example request:

```json
{
  "training_features": [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]],
  "training_targets": [0.0, 1.0, 1.0, 0.0],
  "prediction_features": [[0.1, 0.2], [0.9, 0.8]],
  "feature_map": {"type": "zz_feature_map", "reps": 1, "entanglement": "full"},
  "seed": 7
}
```
