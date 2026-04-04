# Machine Learning VQC Classifier

Use `POST /v1/ml/vqc_classifier` to train a small variational quantum classifier on caller-supplied labeled feature rows and then predict labels for new rows.

Set `QUANTUM_API_BASE_URL` and `QUANTUM_API_KEY` before running the example client code.

Example request:

```json
{
  "training_features": [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]],
  "training_labels": [0, 1, 1, 0],
  "prediction_features": [[0.1, 0.2], [0.9, 0.8]],
  "feature_map": {"type": "zz_feature_map", "reps": 1, "entanglement": "full"},
  "ansatz": {"type": "real_amplitudes", "reps": 1, "entanglement": "reverse_linear"},
  "optimizer": {"name": "cobyla", "maxiter": 25},
  "seed": 7
}
```
