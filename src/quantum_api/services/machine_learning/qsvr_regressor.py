from __future__ import annotations

import numpy as np

from quantum_api.models.machine_learning import QsvrRegressorRequest
from quantum_api.services.machine_learning.common import (
    build_feature_map,
    set_algorithm_seed,
)
from quantum_api.services.qiskit_common.dependencies import ensure_dependency
from quantum_api.services.quantum_runtime import runtime
from quantum_api.services.service_errors import QuantumApiServiceError


def run_qsvr_regressor(request: QsvrRegressorRequest) -> dict[str, object]:
    ensure_dependency(
        available=runtime.qiskit_machine_learning_available,
        provider="qiskit-machine-learning",
        import_error=runtime.qiskit_machine_learning_import_error,
    )

    from qiskit_machine_learning.algorithms import QSVR
    from qiskit_machine_learning.kernels import FidelityQuantumKernel

    training_features = np.asarray(request.training_features, dtype=float)
    prediction_features = np.asarray(request.prediction_features, dtype=float)
    training_targets = np.asarray(request.training_targets, dtype=float)

    set_algorithm_seed(request.seed)
    feature_map = build_feature_map(training_features.shape[1], request.feature_map)
    kernel = FidelityQuantumKernel(feature_map=feature_map)
    regressor = QSVR(quantum_kernel=kernel)
    try:
        regressor.fit(training_features, training_targets)
    except ValueError as exc:
        raise QuantumApiServiceError(
            error="ml_training_failed",
            message=str(exc),
            status_code=400,
        ) from exc

    support_vector_count = int(len(getattr(regressor, "support_", [])))
    if support_vector_count == 0:
        support_vector_count = int(len(getattr(regressor, "support_vectors_", [])))
    return {
        "predictions": [float(value) for value in regressor.predict(prediction_features)],
        "training_score": float(regressor.score(training_features, training_targets)),
        "regression_metadata": {
            "feature_dimension": int(training_features.shape[1]),
            "training_examples": int(training_features.shape[0]),
            "support_vector_count": support_vector_count,
        },
        "provider": "qiskit-machine-learning",
        "backend_mode": "fidelity_quantum_kernel",
    }
