from __future__ import annotations

import pytest

from quantum_api.models.api import NatureGroundStateEnergyRequest
from quantum_api.services.nature.ground_state_energy import compute_ground_state_energy
from quantum_api.services.quantum_runtime import runtime

requires_nature = pytest.mark.skipif(
    not (runtime.qiskit_nature_available and runtime.pyscf_available and runtime.qiskit_algorithms_available),
    reason="Nature dependencies unavailable",
)


def _nature_body() -> dict[str, object]:
    return {
        "atoms": [
            {"symbol": "H", "x": 0.0, "y": 0.0, "z": 0.0},
            {"symbol": "H", "x": 0.0, "y": 0.0, "z": 0.735},
        ],
        "basis": "sto3g",
        "charge": 0,
        "spin": 0,
        "mapper": "jordan_wigner",
        "optimizer": {"name": "cobyla", "maxiter": 5},
        "ansatz": {"type": "real_amplitudes", "reps": 1},
        "seed": 7,
    }


@requires_nature
def test_nature_service_returns_ground_state_summary():
    payload = compute_ground_state_energy(NatureGroundStateEnergyRequest.model_validate(_nature_body()))
    assert isinstance(payload["ground_state_energy"], float)
    assert payload["mapped_problem_summary"]["num_qubits"] >= 1
    assert payload["solver_metadata"]["optimizer"]["name"] == "cobyla"


@requires_nature
def test_nature_endpoint_contract(client):
    response = client.post("/v1/nature/ground_state_energy", json=_nature_body())
    assert response.status_code == 200
    assert response.json()["provider"] == "qiskit-nature"


def test_nature_dependency_missing_returns_503(client, monkeypatch):
    monkeypatch.setattr(runtime, "pyscf_available", False)
    monkeypatch.setattr(runtime, "pyscf_import_error", "missing for test")

    response = client.post("/v1/nature/ground_state_energy", json=_nature_body())
    assert response.status_code == 503
    assert response.json()["error"] == "provider_unavailable"
