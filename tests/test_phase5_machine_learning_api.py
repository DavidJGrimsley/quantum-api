from __future__ import annotations

import pytest

from quantum_api.models.api import KernelClassifierRequest
from quantum_api.services.phase5_machine_learning import run_kernel_classifier
from quantum_api.services.quantum_runtime import runtime

requires_phase5_ml = pytest.mark.skipif(
    not runtime.qiskit_machine_learning_available,
    reason="Phase 5 machine learning dependencies unavailable",
)


def _ml_body() -> dict[str, object]:
    return {
        "training_features": [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]],
        "training_labels": [0, 1, 1, 0],
        "prediction_features": [[0.1, 0.2], [0.9, 0.8]],
        "feature_map": {"type": "zz_feature_map", "reps": 1, "entanglement": "full"},
        "seed": 7,
    }


@requires_phase5_ml
def test_ml_service_returns_predictions_and_training_score():
    payload = run_kernel_classifier(KernelClassifierRequest.model_validate(_ml_body()))
    assert len(payload["predictions"]) == 2
    assert payload["support_vector_count"] >= 1
    assert payload["training_score"] >= 0.0


@requires_phase5_ml
def test_ml_endpoint_contract(client):
    response = client.post("/v1/ml/kernel_classifier", json=_ml_body())
    assert response.status_code == 200
    assert response.json()["provider"] == "qiskit-machine-learning"


def test_ml_validation_rejects_mismatched_label_count(client):
    payload = _ml_body()
    payload["training_labels"] = [0, 1]
    response = client.post("/v1/ml/kernel_classifier", json=payload)
    assert response.status_code == 422


def test_ml_dependency_missing_returns_503(client, monkeypatch):
    monkeypatch.setattr(runtime, "qiskit_machine_learning_available", False)
    monkeypatch.setattr(runtime, "qiskit_machine_learning_import_error", "missing for test")

    response = client.post("/v1/ml/kernel_classifier", json=_ml_body())
    assert response.status_code == 503
    assert response.json()["error"] == "provider_unavailable"
