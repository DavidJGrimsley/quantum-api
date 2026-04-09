from __future__ import annotations

from types import SimpleNamespace

import pytest

from quantum_api.config import get_settings
from quantum_api.main import app
from quantum_api.services.backend_catalog import clear_backend_catalog_cache
from quantum_api.services.quantum_runtime import runtime
from quantum_api.supabase_auth import AuthenticatedUser

requires_qiskit = pytest.mark.skipif(
    not runtime.qiskit_available,
    reason="qiskit runtime unavailable",
)

QASM2_BELL = (
    'OPENQASM 2.0; include "qelib1.inc"; '
    "qreg q[2]; creg c[2]; h q[0]; cx q[0],q[1]; measure q -> c;"
)


def _mock_user(
    monkeypatch,
    *,
    user_id: str,
    expected_token: str = "Bearer test-token",
) -> dict[str, str]:
    async def fake_verify(authorization_header: str | None) -> AuthenticatedUser:
        assert authorization_header == expected_token
        return AuthenticatedUser(
            user_id=user_id,
            email=f"{user_id}@example.test",
            claims={"sub": user_id, "aud": "authenticated"},
        )

    monkeypatch.setattr(app.state.jwt_verifier, "verify_authorization_header", fake_verify)
    return {"Authorization": expected_token}


@requires_qiskit
def test_transpile_contract_with_circuit_input(client):
    response = client.post(
        "/v1/transpile",
        json={
            "circuit": {
                "num_qubits": 2,
                "operations": [
                    {"gate": "h", "target": 0},
                    {"gate": "cx", "control": 0, "target": 1},
                ],
            },
            "backend_name": "aer_simulator",
        },
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["backend_name"] == "aer_simulator"
    assert payload["provider"] == "aer"
    assert payload["input_format"] == "circuit"
    assert payload["qasm_version"] == "3"
    assert "OPENQASM 3" in payload["qasm"]
    assert payload["num_qubits"] == 2
    assert isinstance(payload["operations"], list)
    assert payload["size"] >= 1
    assert payload["depth"] >= 1


@requires_qiskit
def test_transpile_contract_with_qasm_input(client):
    response = client.post(
        "/v1/transpile",
        json={
            "qasm": {"source": QASM2_BELL, "qasm_version": "auto"},
            "backend_name": "aer_simulator",
            "output_qasm_version": "2",
        },
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["backend_name"] == "aer_simulator"
    assert payload["provider"] == "aer"
    assert payload["input_format"] == "qasm"
    assert payload["qasm_version"] == "2"
    assert payload["qasm"].startswith("OPENQASM 2.0;")
    assert payload["num_qubits"] == 2


def test_transpile_validation_rejects_mixed_input(client):
    response = client.post(
        "/v1/transpile",
        json={
            "circuit": {"num_qubits": 1, "operations": [{"gate": "x", "target": 0}]},
            "qasm": {"source": 'OPENQASM 2.0; include "qelib1.inc"; qreg q[1];'},
            "backend_name": "aer_simulator",
        },
    )
    assert response.status_code == 422


@requires_qiskit
def test_transpile_backend_not_found_error(client):
    response = client.post(
        "/v1/transpile",
        json={
            "circuit": {"num_qubits": 1, "operations": [{"gate": "x", "target": 0}]},
            "backend_name": "does_not_exist",
        },
    )
    assert response.status_code == 404
    payload = response.json()
    assert payload["error"] == "backend_not_found"
    assert payload["details"]["backend_name"] == "does_not_exist"


@requires_qiskit
def test_transpile_rejects_backend_qubit_capacity_mismatch(client, monkeypatch):
    class _TinyBackend:
        def configuration(self):
            return SimpleNamespace(
                backend_name="tiny_backend",
                simulator=True,
                n_qubits=1,
                basis_gates=["x"],
                coupling_map=[],
            )

    def fake_resolve_backend(backend_name, provider, *, ibm_credentials=None):
        assert backend_name == "tiny_backend"
        assert provider == "aer"
        assert ibm_credentials is None
        return "aer", _TinyBackend()

    monkeypatch.setattr("quantum_api.services.transpilation.resolve_backend", fake_resolve_backend)

    response = client.post(
        "/v1/transpile",
        json={
            "circuit": {
                "num_qubits": 2,
                "operations": [{"gate": "x", "target": 1}],
            },
            "backend_name": "tiny_backend",
            "provider": "aer",
        },
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["error"] == "backend_qubit_capacity_exceeded"
    assert payload["details"]["backend_name"] == "tiny_backend"
    assert payload["details"]["provider"] == "aer"
    assert payload["details"]["requested_qubits"] == 2
    assert payload["details"]["available_qubits"] == 1


@requires_qiskit
def test_transpile_rejects_legacy_aer_backend_aliases(client):
    response = client.post(
        "/v1/transpile",
        json={
            "circuit": {"num_qubits": 1, "operations": [{"gate": "x", "target": 0}]},
            "backend_name": "qasm_simulator",
            "provider": "aer",
        },
    )
    assert response.status_code == 404
    payload = response.json()
    assert payload["error"] == "backend_not_found"
    assert payload["details"]["backend_name"] == "qasm_simulator"


@requires_qiskit
def test_transpile_provider_ibm_unavailable_without_config(client, monkeypatch):
    monkeypatch.setenv("IBM_TOKEN", "")
    monkeypatch.setenv("IBM_INSTANCE", "")
    get_settings.cache_clear()
    clear_backend_catalog_cache()

    response = client.post(
        "/v1/transpile",
        json={
            "circuit": {"num_qubits": 1, "operations": [{"gate": "x", "target": 0}]},
            "backend_name": "ibm_fake_backend",
            "provider": "ibm",
        },
    )
    assert response.status_code == 503
    payload = response.json()
    assert payload["error"] == "provider_credentials_missing"
    assert payload["details"]["reason"] in {"missing_credentials", "no_default_profile"}

    get_settings.cache_clear()
    clear_backend_catalog_cache()


@requires_qiskit
def test_transpile_provider_ibm_uses_stored_profile(unauth_client, monkeypatch):
    headers = _mock_user(monkeypatch, user_id="transpile-ibm-user")
    created_profile = unauth_client.post(
        "/v1/ibm/profiles",
        json={
            "profile_name": "IBM Open",
            "token": "tok_1234567890abcdef",
            "instance": "crn:v1:bluemix:public:quantum-computing:us-east:a/test::",
            "is_default": True,
        },
        headers=headers,
    )
    assert created_profile.status_code == 200

    created_key = unauth_client.post("/v1/keys", json={"name": "transpile"}, headers=headers)
    assert created_key.status_code == 200
    raw_key = created_key.json()["raw_key"]

    def fake_resolve_backend(backend_name, provider, *, ibm_credentials=None):
        assert backend_name == "ibm_fake_backend"
        assert provider == "ibm"
        assert ibm_credentials is not None
        assert ibm_credentials.owner_user_id == "transpile-ibm-user"
        assert ibm_credentials.profile_name == "IBM Open"
        return "ibm", object()

    monkeypatch.setattr("quantum_api.services.transpilation.resolve_backend", fake_resolve_backend)
    monkeypatch.setattr(
        "quantum_api.services.transpilation.runtime.transpile",
        lambda circuit, backend, optimization_level=1, seed_transpiler=None: circuit,
    )

    response = unauth_client.post(
        "/v1/transpile",
        json={
            "circuit": {
                "num_qubits": 2,
                "operations": [
                    {"gate": "h", "target": 0},
                    {"gate": "cx", "control": 0, "target": 1},
                ],
            },
            "backend_name": "ibm_fake_backend",
            "provider": "ibm",
            "ibm_profile": "IBM Open",
        },
        headers={"X-API-Key": raw_key},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "ibm"
    assert payload["backend_name"] == "ibm_fake_backend"
    assert payload["input_format"] == "circuit"


@requires_qiskit
def test_transpile_seeded_output_is_stable(client):
    payload = {
        "circuit": {
            "num_qubits": 2,
            "operations": [
                {"gate": "h", "target": 0},
                {"gate": "cx", "control": 0, "target": 1},
                {"gate": "ry", "target": 0, "theta": 1.3},
            ],
        },
        "backend_name": "aer_simulator",
        "optimization_level": 2,
        "seed_transpiler": 11,
    }

    first = client.post("/v1/transpile", json=payload)
    second = client.post("/v1/transpile", json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["operations"] == second.json()["operations"]
