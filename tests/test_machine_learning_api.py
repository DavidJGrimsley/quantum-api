from __future__ import annotations

import pytest

from quantum_api.models.api import (
    KernelClassifierRequest,
    QsvrRegressorRequest,
    VqcClassifierRequest,
)
from quantum_api.services.machine_learning.kernel_classifier import run_kernel_classifier
from quantum_api.services.machine_learning.qsvr_regressor import run_qsvr_regressor
from quantum_api.services.machine_learning.vqc_classifier import run_vqc_classifier
from quantum_api.services.quantum_runtime import runtime

requires_machine_learning = pytest.mark.skipif(
    not runtime.qiskit_machine_learning_available,
    reason="Machine-learning dependencies unavailable",
)


def _ml_body() -> dict[str, object]:
    return {
        "training_features": [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]],
        "training_labels": [0, 1, 1, 0],
        "prediction_features": [[0.1, 0.2], [0.9, 0.8]],
        "feature_map": {"type": "zz_feature_map", "reps": 1, "entanglement": "full"},
        "seed": 7,
    }


def _vqc_body() -> dict[str, object]:
    return {
        "training_features": [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]],
        "training_labels": [0, 1, 1, 0],
        "prediction_features": [[0.1, 0.2], [0.9, 0.8]],
        "feature_map": {"type": "zz_feature_map", "reps": 1, "entanglement": "full"},
        "ansatz": {"type": "real_amplitudes", "reps": 1, "entanglement": "reverse_linear"},
        "optimizer": {"name": "cobyla", "maxiter": 5},
        "seed": 7,
    }


def _qsvr_body() -> dict[str, object]:
    return {
        "training_features": [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]],
        "training_targets": [0.0, 1.0, 1.0, 0.0],
        "prediction_features": [[0.1, 0.2], [0.9, 0.8]],
        "feature_map": {"type": "zz_feature_map", "reps": 1, "entanglement": "full"},
        "seed": 7,
    }


@requires_machine_learning
def test_ml_service_returns_predictions_and_training_score():
    payload = run_kernel_classifier(KernelClassifierRequest.model_validate(_ml_body()))
    assert len(payload["predictions"]) == 2
    assert payload["support_vector_count"] >= 1
    assert payload["training_score"] >= 0.0


@requires_machine_learning
def test_vqc_service_returns_predictions_and_model_metadata():
    payload = run_vqc_classifier(VqcClassifierRequest.model_validate(_vqc_body()))
    assert len(payload["predictions"]) == 2
    assert payload["training_score"] >= 0.0
    assert payload["model_metadata"]["ansatz_parameters"] >= 1


@requires_machine_learning
def test_qsvr_service_returns_predictions_and_regression_metadata():
    payload = run_qsvr_regressor(QsvrRegressorRequest.model_validate(_qsvr_body()))
    assert len(payload["predictions"]) == 2
    assert payload["training_score"] >= 0.0
    assert payload["regression_metadata"]["support_vector_count"] >= 1


@requires_machine_learning
def test_ml_endpoint_contract(client):
    response = client.post("/v1/ml/kernel_classifier", json=_ml_body())
    assert response.status_code == 200
    assert response.json()["provider"] == "qiskit-machine-learning"

    vqc = client.post("/v1/ml/vqc_classifier", json=_vqc_body())
    assert vqc.status_code == 200
    assert vqc.json()["backend_mode"] == "statevector_sampler_vqc"

    qsvr = client.post("/v1/ml/qsvr_regressor", json=_qsvr_body())
    assert qsvr.status_code == 200
    assert len(qsvr.json()["predictions"]) == 2


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


def test_ml_seeded_kernel_classifier_dependency_missing_returns_503(client, monkeypatch):
    monkeypatch.setattr(runtime, "qiskit_algorithms_available", False)
    monkeypatch.setattr(runtime, "qiskit_algorithms_import_error", "missing for test")

    response = client.post("/v1/ml/kernel_classifier", json=_ml_body())
    assert response.status_code == 503
    assert response.json()["error"] == "provider_unavailable"


def test_vqc_dependency_missing_returns_503(client, monkeypatch):
    monkeypatch.setattr(runtime, "qiskit_algorithms_available", False)
    monkeypatch.setattr(runtime, "qiskit_algorithms_import_error", "missing for test")

    response = client.post("/v1/ml/vqc_classifier", json=_vqc_body())
    assert response.status_code == 503
    assert response.json()["error"] == "provider_unavailable"


def test_qsvr_validation_rejects_mismatched_target_count(client):
    payload = _qsvr_body()
    payload["training_targets"] = [0.0, 1.0]
    response = client.post("/v1/ml/qsvr_regressor", json=payload)
    assert response.status_code == 422


@requires_machine_learning
def test_qsvr_results_are_stable():
    first = run_qsvr_regressor(QsvrRegressorRequest.model_validate(_qsvr_body()))
    second = run_qsvr_regressor(QsvrRegressorRequest.model_validate(_qsvr_body()))
    assert first["predictions"] == second["predictions"]
