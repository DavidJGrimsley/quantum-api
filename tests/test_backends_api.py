from __future__ import annotations

from types import SimpleNamespace

import pytest

from quantum_api.config import get_settings
from quantum_api.services.backend_catalog import clear_backend_catalog_cache
from quantum_api.services.quantum_runtime import runtime

requires_qiskit = pytest.mark.skipif(
    not runtime.qiskit_available,
    reason="qiskit runtime unavailable",
)


@requires_qiskit
def test_list_backends_contract(client):
    response = client.get("/v1/list_backends")
    assert response.status_code == 200

    payload = response.json()
    assert "backends" in payload
    assert payload["total"] == len(payload["backends"])
    assert payload["filters_applied"]["provider"] is None
    assert payload["filters_applied"]["simulator_only"] is False
    assert payload["filters_applied"]["min_qubits"] == 1
    assert any(item["provider"] == "aer" for item in payload["backends"])


@requires_qiskit
def test_list_backends_filtering(client):
    response = client.get("/v1/list_backends?provider=aer&simulator_only=true&min_qubits=31")
    assert response.status_code == 200

    payload = response.json()
    assert payload["filters_applied"]["provider"] == "aer"
    assert payload["filters_applied"]["simulator_only"] is True
    assert payload["filters_applied"]["min_qubits"] == 31
    assert all(item["provider"] == "aer" for item in payload["backends"])
    assert all(item["is_simulator"] for item in payload["backends"])
    assert all(item["num_qubits"] >= 31 for item in payload["backends"])


@requires_qiskit
def test_list_backends_provider_ibm_unavailable_without_config(client, monkeypatch):
    monkeypatch.setenv("IBM_TOKEN", "")
    monkeypatch.setenv("IBM_INSTANCE", "")
    get_settings.cache_clear()
    clear_backend_catalog_cache()

    response = client.get("/v1/list_backends?provider=ibm")
    assert response.status_code == 503
    payload = response.json()
    assert payload["error"] == "provider_credentials_missing"
    assert payload["details"]["reason"] in {"missing_credentials", "no_default_profile"}

    get_settings.cache_clear()
    clear_backend_catalog_cache()


@requires_qiskit
def test_list_backends_simulated_ibm_listing(client, monkeypatch):
    class FakeBackend:
        def configuration(self):
            return SimpleNamespace(
                backend_name="ibm_fake_backend",
                simulator=False,
                n_qubits=127,
                basis_gates=["x", "rz", "sx", "cx"],
                coupling_map=[(0, 1), (1, 2)],
            )

    monkeypatch.setenv("IBM_TOKEN", "ibm-token")
    monkeypatch.setenv("IBM_INSTANCE", "instance-crn")
    get_settings.cache_clear()
    clear_backend_catalog_cache()
    monkeypatch.setattr("quantum_api.services.backend_catalog._list_ibm_backends", lambda _credentials: [FakeBackend()])

    response = client.get("/v1/list_backends?provider=ibm")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    backend = payload["backends"][0]
    assert backend["provider"] == "ibm"
    assert backend["name"] == "ibm_fake_backend"
    assert backend["is_hardware"] is True
    assert backend["num_qubits"] == 127
    assert backend["coupling_map_summary"]["present"] is True

    monkeypatch.setenv("IBM_TOKEN", "")
    monkeypatch.setenv("IBM_INSTANCE", "")
    get_settings.cache_clear()
    clear_backend_catalog_cache()


def test_list_backends_validation_invalid_provider(client):
    response = client.get("/v1/list_backends?provider=invalid")
    assert response.status_code == 422


@requires_qiskit
def test_list_backends_validation_invalid_min_qubits(client):
    response = client.get("/v1/list_backends?min_qubits=0")
    assert response.status_code == 422
