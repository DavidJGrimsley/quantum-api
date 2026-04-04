from __future__ import annotations

import numpy as np

from quantum_api.models.machine_learning import KernelClassifierRequest
from quantum_api.services.phase2_errors import Phase2ServiceError
from quantum_api.services.qiskit_common.dependencies import ensure_dependency
from quantum_api.services.quantum_runtime import runtime


def run_kernel_classifier(request: KernelClassifierRequest) -> dict[str, object]:
    ensure_dependency(
        available=runtime.qiskit_machine_learning_available,
        provider="qiskit-machine-learning",
        import_error=runtime.qiskit_machine_learning_import_error,
    )

    from qiskit.circuit.library import zz_feature_map
    from qiskit_machine_learning.algorithms import QSVC
    from qiskit_machine_learning.kernels import FidelityQuantumKernel

    training_features = np.asarray(request.training_features, dtype=float)
    prediction_features = np.asarray(request.prediction_features, dtype=float)
    training_labels = np.asarray(request.training_labels)

    feature_map = zz_feature_map(
        training_features.shape[1],
        reps=request.feature_map.reps,
        entanglement=request.feature_map.entanglement,
    )
    kernel = FidelityQuantumKernel(feature_map=feature_map)
    classifier = QSVC(quantum_kernel=kernel)
    try:
        classifier.fit(training_features, training_labels)
    except ValueError as exc:
        raise Phase2ServiceError(
            error="ml_training_failed",
            message=str(exc),
            status_code=400,
        ) from exc

    predictions = classifier.predict(prediction_features)
    support_vector_count = int(len(getattr(classifier, "support_", [])))
    if support_vector_count == 0:
        support_vector_count = int(len(getattr(classifier, "support_vectors_", [])))
    return {
        "predictions": [item.item() if hasattr(item, "item") else item for item in predictions],
        "training_score": float(classifier.score(training_features, training_labels)),
        "support_vector_count": support_vector_count,
        "training_metadata": {
            "classes": [item.item() if hasattr(item, "item") else item for item in classifier.classes_],
            "feature_dimension": int(training_features.shape[1]),
            "training_examples": int(training_features.shape[0]),
        },
        "provider": "qiskit-machine-learning",
        "backend_mode": "fidelity_quantum_kernel",
    }
