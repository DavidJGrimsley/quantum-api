from __future__ import annotations

import numpy as np

from quantum_api.models.machine_learning import VqcClassifierRequest
from quantum_api.services.machine_learning.common import (
    build_ansatz,
    build_feature_map,
    python_list,
    set_algorithm_seed,
)
from quantum_api.services.service_errors import QuantumApiServiceError
from quantum_api.services.qiskit_common.dependencies import ensure_dependency
from quantum_api.services.qiskit_common.optimizers import (
    build_optimizer,
    optimizer_metadata_from_result,
)
from quantum_api.services.quantum_runtime import runtime


def run_vqc_classifier(request: VqcClassifierRequest) -> dict[str, object]:
    ensure_dependency(
        available=runtime.qiskit_machine_learning_available,
        provider="qiskit-machine-learning",
        import_error=runtime.qiskit_machine_learning_import_error,
    )
    ensure_dependency(
        available=runtime.qiskit_algorithms_available,
        provider="qiskit-algorithms",
        import_error=runtime.qiskit_algorithms_import_error,
    )

    from qiskit.primitives import StatevectorSampler
    from qiskit_machine_learning.algorithms import VQC

    training_features = np.asarray(request.training_features, dtype=float)
    prediction_features = np.asarray(request.prediction_features, dtype=float)
    training_labels = np.asarray(request.training_labels)

    set_algorithm_seed(request.seed)
    feature_map = build_feature_map(training_features.shape[1], request.feature_map)
    ansatz = build_ansatz(training_features.shape[1], request.ansatz)
    classifier = VQC(
        feature_map=feature_map,
        ansatz=ansatz,
        optimizer=build_optimizer(request.optimizer),
        sampler=StatevectorSampler(seed=request.seed),
    )
    try:
        classifier.fit(training_features, training_labels)
    except ValueError as exc:
        raise QuantumApiServiceError(
            error="ml_training_failed",
            message=str(exc),
            status_code=400,
        ) from exc

    predictions = classifier.predict(prediction_features)
    labels = list(dict.fromkeys(python_list(training_labels)))
    fit_result = classifier.fit_result
    return {
        "predictions": python_list(predictions),
        "training_score": float(classifier.score(training_features, training_labels)),
        "class_metadata": {
            "labels": labels,
            "num_classes": int(classifier.num_classes),
            "feature_dimension": int(training_features.shape[1]),
            "training_examples": int(training_features.shape[0]),
        },
        "model_metadata": {
            "ansatz_parameters": int(ansatz.num_parameters),
            "final_weights": [float(value) for value in classifier.weights],
            "optimizer": optimizer_metadata_from_result(
                name=request.optimizer.name,
                maxiter=request.optimizer.maxiter,
                result=fit_result,
            ).model_dump(mode="json"),
        },
        "provider": "qiskit-machine-learning",
        "backend_mode": "statevector_sampler_vqc",
    }
