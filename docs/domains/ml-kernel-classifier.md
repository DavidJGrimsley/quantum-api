# ML Kernel Classifier

Use `POST /v1/ml/kernel_classifier` to fit a request-scoped QSVC model with a quantum kernel and return predictions for the supplied inference rows.

Set `QUANTUM_API_BASE_URL` and `QUANTUM_API_KEY` before running the example client code.

Example request:

```json
{
  "training_features": [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]],
  "training_labels": [0, 1, 1, 0],
  "prediction_features": [[0.1, 0.2], [0.9, 0.8]],
  "feature_map": {"type": "zz_feature_map", "reps": 1, "entanglement": "full"},
  "seed": 7
}
```
