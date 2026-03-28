from quantum_api.config import get_settings
from quantum_api.services.quantum_runtime import runtime


def test_health_contract(client):
    response = client.get("/v1/health")
    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "healthy"
    assert payload["service"] == "Quantum API"
    assert "version" in payload
    assert "qiskit_available" in payload
    assert payload["runtime_mode"] in {"qiskit", "classical-fallback"}


def test_echo_types_contract(client):
    response = client.get("/v1/echo-types")
    assert response.status_code == 200
    payload = response.json()
    assert "echo_types" in payload
    assert any(item["name"] == "quantum_interference" for item in payload["echo_types"])


def test_gate_run_contract_bit_flip(client):
    response = client.post("/v1/gates/run", json={"gate_type": "bit_flip"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["gate_type"] == "bit_flip"
    assert payload["measurement"] in {0, 1}
    assert isinstance(payload["superposition_strength"], float)
    assert isinstance(payload["success"], bool)


def test_gate_run_rotation_requires_angle(client):
    response = client.post("/v1/gates/run", json={"gate_type": "rotation"})
    assert response.status_code == 422


def test_gate_run_rotation_contract(client):
    response = client.post(
        "/v1/gates/run",
        json={"gate_type": "rotation", "rotation_angle_rad": 1.57079632679},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["gate_type"] == "rotation"
    assert 0.0 <= payload["superposition_strength"] <= 1.0


def test_text_transform_contract(client):
    response = client.post("/v1/text/transform", json={"text": "memory signal and quantum circuit"})
    assert response.status_code == 200
    payload = response.json()

    assert payload["original"]
    assert payload["transformed"]
    assert isinstance(payload["coverage_percent"], float)
    assert isinstance(payload["quantum_words"], int)
    assert isinstance(payload["total_words"], int)
    assert isinstance(payload["category_counts"], dict)


def test_text_transform_validation(client):
    response = client.post("/v1/text/transform", json={})
    assert response.status_code == 422


def test_text_transform_length_guardrail(client):
    max_length = get_settings().max_text_length
    long_text = "a" * (max_length + 1)
    response = client.post("/v1/text/transform", json={"text": long_text})
    assert response.status_code == 422


def test_qiskit_unavailable_mode(client, monkeypatch):
    monkeypatch.setenv("REQUIRE_QISKIT", "true")
    get_settings.cache_clear()

    old_value = runtime.qiskit_available
    runtime.qiskit_available = False

    response = client.post("/v1/gates/run", json={"gate_type": "bit_flip"})
    assert response.status_code == 503

    runtime.qiskit_available = old_value
    monkeypatch.delenv("REQUIRE_QISKIT", raising=False)
    get_settings.cache_clear()


def test_invalid_gate_type(client):
    response = client.post("/v1/gates/run", json={"gate_type": "invalid_gate"})
    assert response.status_code == 422
