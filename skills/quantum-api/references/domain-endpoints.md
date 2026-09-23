# Quantum API — Domain Endpoints (Phase 5)

Phase 5 endpoints require additional Python dependencies installed as extras.
They are unavailable (return `503`) if the required extra is not installed on
the server.

**Auth**: All domain endpoints require `X-API-Key`.

---

## Installation Extras

```bash
# Install all Phase 5 extras:
uv sync --extra phase5-optimization --extra phase5-experiments \
        --extra phase5-finance --extra phase5-ml --extra phase5-nature

# Or individually:
uv sync --extra phase5-optimization   # QAOA, VQE, knapsack, MaxCut, TSP
uv sync --extra phase5-experiments    # state tomography, benchmarking, T1/T2, QV
uv sync --extra phase5-finance        # portfolio optimization/diversification
uv sync --extra phase5-ml             # kernel classifier, QSVR, VQC classifier
uv sync --extra phase5-nature         # ground state energy, fermionic mapping
```

---

## Optimization

### `POST /v1/optimization/qaoa`
QAOA (Quantum Approximate Optimization Algorithm).

Example request (a binary quadratic problem):

```json
{
  "problem": {
    "num_variables": 2,
    "linear": [1.0, -2.0],
    "quadratic": [{"i": 0, "j": 1, "value": 2.0}],
    "sense": "minimize"
  },
  "reps": 1,
  "optimizer": {"name": "cobyla", "maxiter": 25},
  "shots": 512,
  "seed": 7
}
```

Illustrative response (values vary by problem and execution):

```json
{
  "best_bitstring": "01",
  "objective_value": -2.0,
  "solution_samples": [
    {"bitstring": "01", "objective_value": -2.0, "probability": 0.6, "status": "SUCCESS"}
  ],
  "optimizer_metadata": {
    "name": "cobyla",
    "maxiter": 25,
    "evaluations": 30,
    "optimizer_time_seconds": 0.2
  },
  "provider": "qiskit-algorithms",
  "backend_mode": "statevector_sampler",
  "warnings": null
}
```

### `POST /v1/optimization/vqe`
VQE (Variational Quantum Eigensolver) for ground state energy.

Refer to domain doc: [`docs/domains/optimization-vqe.md`](../../../docs/domains/optimization-vqe.md)

Additional routes: `POST /v1/optimization/knapsack`,
`POST /v1/optimization/maxcut`, and `POST /v1/optimization/tsp`.
See [the domain guides](../../../docs/domains/) for their payloads.

---

## Experiments

### `POST /v1/experiments/state_tomography`
Quantum state tomography.

Refer to: [`docs/domains/experiments-state-tomography.md`](../../../docs/domains/experiments-state-tomography.md)

### `POST /v1/experiments/randomized_benchmarking`
Randomized benchmarking of gate fidelity.

Refer to: [`docs/domains/experiments-randomized-benchmarking.md`](../../../docs/domains/experiments-randomized-benchmarking.md)

Additional routes: `POST /v1/experiments/quantum_volume`,
`POST /v1/experiments/t1`, and `POST /v1/experiments/t2ramsey`. See the
[Quantum Volume](../../../docs/domains/experiments-quantum-volume.md),
[T1](../../../docs/domains/experiments-t1.md), and
[T2 Ramsey](../../../docs/domains/experiments-t2ramsey.md) guides.

---

## Finance

### `POST /v1/finance/portfolio_optimization`
Quantum portfolio optimization.

Refer to: [`docs/domains/finance-portfolio-optimization.md`](../../../docs/domains/finance-portfolio-optimization.md)

Also available: `POST /v1/finance/portfolio_diversification`; see the
[diversification guide](../../../docs/domains/finance-portfolio-diversification.md).

---

## Machine Learning

### `POST /v1/ml/kernel_classifier`
Quantum kernel-based classifier (QSVC).

Refer to: [`docs/domains/ml-kernel-classifier.md`](../../../docs/domains/ml-kernel-classifier.md)

Additional routes: `POST /v1/ml/qsvr_regressor` and
`POST /v1/ml/vqc_classifier`; see
the [QSVR](../../../docs/domains/ml-qsvr-regressor.md) and
[VQC](../../../docs/domains/ml-vqc-classifier.md) guides.

---

## Nature (Quantum Chemistry)

### `POST /v1/nature/ground_state_energy`
Ground state energy estimation (VQE + PySCF driver).

Requires `phase5-nature` extra (includes `pyscf`, `qiskit-nature`, `qiskit-nature-pyscf`).

Refer to: [`docs/domains/nature-ground-state-energy.md`](../../../docs/domains/nature-ground-state-energy.md)

Also available: `POST /v1/nature/fermionic_mapping_preview`; see the
[mapping guide](../../../docs/domains/nature-fermionic-mapping-preview.md).

---

## Algorithms

The following algorithms have direct REST endpoints. Read the linked guides or
current OpenAPI schema for payloads:

- `POST /v1/algorithms/amplitude_estimation`: [guide](../../../docs/domains/algorithms-amplitude-estimation.md)
- `POST /v1/algorithms/grover_search`: [guide](../../../docs/domains/algorithms-grover-search.md)
- `POST /v1/algorithms/phase_estimation`: [guide](../../../docs/domains/algorithms-phase-estimation.md)
- `POST /v1/algorithms/time_evolution`: [guide](../../../docs/domains/algorithms-time-evolution.md)

---

## Checking Availability

`GET /v1/health` reports base Qiskit availability only. It does not report
which Phase 5 extras are installed. Call the desired endpoint and handle a
`503 provider_unavailable` if its dependency is missing; the response names
the unavailable provider and includes `details.reason`.

For example, if `qiskit-algorithms` is unavailable:

```json
{
  "error": "provider_unavailable",
  "message": "Provider 'qiskit-algorithms' is unavailable.",
  "details": {"reason": "missing_dependency"},
  "request_id": "..."
}
```
