from __future__ import annotations

from quantum_api.models.algorithms import AmplitudeEstimationRequest
from quantum_api.services.algorithms.common import (
    build_circuit,
    build_sampler,
    serialize_confidence_interval,
    serialize_samples,
)
from quantum_api.services.qiskit_common.dependencies import ensure_dependency
from quantum_api.services.quantum_runtime import runtime


def run_amplitude_estimation(request: AmplitudeEstimationRequest) -> dict[str, object]:
    ensure_dependency(
        available=runtime.qiskit_algorithms_available,
        provider="qiskit-algorithms",
        import_error=runtime.qiskit_algorithms_import_error,
    )

    from qiskit_algorithms import (
        AmplitudeEstimation,
        EstimationProblem,
        FasterAmplitudeEstimation,
        IterativeAmplitudeEstimation,
        MaximumLikelihoodAmplitudeEstimation,
    )

    sampler = build_sampler(shots=request.shots, seed=request.seed)
    if request.variant == "ae":
        algorithm = AmplitudeEstimation(num_eval_qubits=request.num_eval_qubits, sampler=sampler)
    elif request.variant == "iae":
        algorithm = IterativeAmplitudeEstimation(
            epsilon_target=request.epsilon_target,
            alpha=request.alpha,
            sampler=sampler,
        )
    elif request.variant == "fae":
        algorithm = FasterAmplitudeEstimation(
            delta=request.delta,
            maxiter=request.maxiter,
            rescale=request.rescale,
            sampler=sampler,
        )
    else:
        algorithm = MaximumLikelihoodAmplitudeEstimation(
            evaluation_schedule=request.evaluation_schedule,
            sampler=sampler,
        )

    problem = EstimationProblem(
        state_preparation=build_circuit(request.state_preparation),
        objective_qubits=request.objective_qubits,
        grover_operator=build_circuit(request.grover_operator),
    )
    result = algorithm.estimate(problem)

    processed_estimate = getattr(result, "estimation_processed", None)
    if processed_estimate is None:
        processed_estimate = getattr(result, "processed_estimation", None)
    mle = result.mle
    mle_processed = result.mle_processed
    return {
        "estimate": float(result.estimation),
        "processed_estimate": float(processed_estimate) if processed_estimate is not None else None,
        "confidence_interval": serialize_confidence_interval(result.confidence_interval),
        "variant": request.variant,
        "provider": "qiskit-algorithms",
        "backend_mode": "statevector_sampler",
        "raw_metadata": {
            "num_oracle_queries": int(result.num_oracle_queries),
            "samples": serialize_samples(result.samples),
            "samples_processed": serialize_samples(result.samples_processed),
            "mle": float(mle) if mle is not None else None,
            "mle_processed": float(mle_processed) if mle_processed is not None else None,
        },
    }
