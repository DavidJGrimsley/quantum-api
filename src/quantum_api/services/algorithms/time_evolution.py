from __future__ import annotations

import numpy as np

from quantum_api.models.algorithms import TimeEvolutionRequest
from quantum_api.services.algorithms.common import (
    build_aux_operators,
    build_circuit,
    build_estimator,
    build_sampler,
    serialize_aux_operator_values,
    serialize_evolved_state,
)
from quantum_api.services.service_errors import QuantumApiServiceError
from quantum_api.services.qiskit_common.dependencies import ensure_dependency
from quantum_api.services.qiskit_common.operators import sparse_pauli_op_from_terms
from quantum_api.services.qiskit_common.optimizers import build_optimizer
from quantum_api.services.qiskit_common.serialization import json_safe_value
from quantum_api.services.quantum_runtime import runtime


def _final_parameters_payload(value: object) -> list[float] | None:
    if value is None:
        return None
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return [float(value)]
        if value.ndim == 1:
            return [float(item) for item in value]
        return [float(item) for item in value[-1]]

    items = list(value) if not isinstance(value, (str, bytes)) else [value]
    if not items:
        return None

    final_item = items[-1]
    if isinstance(final_item, np.ndarray):
        return [float(item) for item in final_item]
    if isinstance(final_item, (list, tuple)):
        return [float(item) for item in final_item]
    return [float(final_item)]


def run_time_evolution(request: TimeEvolutionRequest) -> dict[str, object]:
    ensure_dependency(
        available=runtime.qiskit_algorithms_available,
        provider="qiskit-algorithms",
        import_error=runtime.qiskit_algorithms_import_error,
    )

    from qiskit.circuit.library import real_amplitudes
    from qiskit_algorithms import PVQD, TrotterQRTE, VarQITE, VarQRTE
    from qiskit_algorithms.state_fidelities import ComputeUncompute
    from qiskit_algorithms.time_evolvers import TimeEvolutionProblem

    hamiltonian = sparse_pauli_op_from_terms(request.hamiltonian)
    aux_operators, aux_operator_names = build_aux_operators(request.aux_operators)
    estimator = build_estimator(seed=request.seed)
    num_timesteps = request.num_timesteps or 1

    if request.variant == "trotter_qrte":
        problem = TimeEvolutionProblem(
            hamiltonian,
            time=request.time,
            initial_state=build_circuit(request.initial_state),
            aux_operators=aux_operators,
        )
        result = TrotterQRTE(estimator=estimator, num_timesteps=num_timesteps).evolve(problem)
        backend_mode = "statevector_estimator"
    else:
        ansatz = real_amplitudes(
            hamiltonian.num_qubits,
            reps=request.ansatz.reps,
            entanglement=request.ansatz.entanglement,
        )
        initial_parameters = np.asarray(request.initial_parameters, dtype=float)
        if len(initial_parameters) != ansatz.num_parameters:
            raise QuantumApiServiceError(
                error="invalid_initial_parameters",
                message="initial_parameters length must match the generated ansatz parameter count.",
                status_code=400,
                details={"expected": ansatz.num_parameters, "received": int(len(initial_parameters))},
            )
        problem = TimeEvolutionProblem(
            hamiltonian,
            time=request.time,
            aux_operators=aux_operators,
        )
        if request.variant == "var_qrte":
            result = VarQRTE(
                ansatz=ansatz,
                initial_parameters=initial_parameters,
                estimator=estimator,
                num_timesteps=num_timesteps,
            ).evolve(problem)
            backend_mode = "statevector_estimator"
        elif request.variant == "var_qite":
            result = VarQITE(
                ansatz=ansatz,
                initial_parameters=initial_parameters,
                estimator=estimator,
                num_timesteps=num_timesteps,
            ).evolve(problem)
            backend_mode = "statevector_estimator"
        else:
            result = PVQD(
                fidelity=ComputeUncompute(sampler=build_sampler(shots=request.shots, seed=request.seed)),
                ansatz=ansatz,
                initial_parameters=initial_parameters,
                estimator=estimator,
                optimizer=build_optimizer(request.optimizer),
                num_timesteps=num_timesteps,
            ).evolve(problem)
            backend_mode = "statevector_estimator_sampler"

    final_state_operations, final_statevector = serialize_evolved_state(result.evolved_state)
    parameter_history = getattr(result, "parameters", None)
    if parameter_history is None:
        parameter_history = getattr(result, "parameter_values", None)
    final_parameters = _final_parameters_payload(parameter_history)

    times = getattr(result, "times", None)
    fidelities = getattr(result, "fidelities", None)
    aux_ops_evaluated = getattr(result, "aux_ops_evaluated", None)
    estimated_error = getattr(result, "estimated_error", None)
    observables = getattr(result, "observables", None)

    return {
        "final_state_operations": final_state_operations,
        "final_statevector": final_statevector,
        "times": [float(value) for value in times] if times is not None else None,
        "aux_operator_values": serialize_aux_operator_values(
            aux_ops_evaluated,
            aux_operator_names,
        ),
        "final_parameters": final_parameters,
        "fidelities": [float(value) for value in fidelities] if fidelities is not None else None,
        "variant": request.variant,
        "provider": "qiskit-algorithms",
        "backend_mode": backend_mode,
        "raw_metadata": {
            "estimated_error": float(estimated_error) if estimated_error is not None else None,
            "observables": json_safe_value(observables),
        },
    }
