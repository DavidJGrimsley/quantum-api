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

```json
// Request
{
  "problem_type": "maxcut",
  "graph_edges": [[0, 1], [1, 2], [2, 0]],
  "p": 1,
  "shots": 1024
}

// Response
{
  "optimal_value": 3.0,
  "optimal_parameters": [...],
  "bitstring": "101",
  "counts": { "101": 512, "010": 512 },
  "backend_mode": "qiskit"
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

Before calling Phase 5 endpoints, confirm `runtime_mode` and whether the relevant extra is installed:

```http
GET /v1/health
```

If a Phase 5 endpoint is hit on a server without the required extra:
```json
{
  "error": "feature_unavailable",
  "message": "This endpoint requires the phase5-optimization extra.",
  "request_id": "..."
}
```
