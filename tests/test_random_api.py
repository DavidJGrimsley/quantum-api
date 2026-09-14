from types import SimpleNamespace

import pytest

from quantum_api.config import get_settings
from quantum_api.services.quantum_runtime import runtime
from quantum_api.services.randomness import (
    RandomResultError,
    bounded_value,
    generate_random,
    random_job_shots,
    random_value_from_result,
)


@pytest.mark.parametrize("value", [0, 1])
@pytest.mark.parametrize("qiskit_available", [False, True])
def test_local_coin_contract(client, monkeypatch, value, qiskit_available):
    monkeypatch.setattr(runtime, "qiskit_available", qiskit_available)
    monkeypatch.setattr(get_settings(), "require_qiskit", False)
    monkeypatch.setattr("quantum_api.services.quantum_core.Qubit.measure", lambda self: value)
    response = client.post("/v1/random", json={"min": 0, "max": 1})
    assert response.status_code == 200
    assert response.json() == {
        "value": value,
        "source": "qiskit-simulator" if qiskit_available else "classical-fallback",
    }


@pytest.mark.parametrize("minimum,maximum,bits,expected", [
    (0, 2, [1, 1, 1, 0], 2),  # Reject 3, accept the inclusive upper bound.
    (-2, 0, [1, 1, 0, 0], -2),
    (-1, 1, [1, 1, 0, 1], 0),
    (-2147483648, 2147483647, [1] * 32, 2147483647),
    (-2147483648, 2147483647, [0] * 32, -2147483648),
    (5, 5, [], 5),
])
def test_rejection_sampling(minimum, maximum, bits, expected):
    assert bounded_value(bits, minimum, maximum) == expected


def test_local_reuses_one_qubit_and_measures_each_hadamard(monkeypatch):
    events = []
    bits = iter([1, 1, 0, 1])

    class FakeQubit:
        def __init__(self):
            events.append("create")

        def hadamard(self):
            events.append("h")

        def measure(self):
            events.append("measure")
            return next(bits)

    monkeypatch.setattr("quantum_api.services.randomness.Qubit", FakeQubit)
    assert generate_random(-1, 1).value == 0
    assert events == ["create"] + ["h", "measure"] * 4


@pytest.mark.parametrize("value", [-2147483648, 0, 2147483647])
def test_singleton_does_not_measure(client, monkeypatch, value):
    def unexpected_measure(self):
        pytest.fail("Singleton local requests must not measure")

    monkeypatch.setattr("quantum_api.services.quantum_core.Qubit.measure", unexpected_measure)
    response = client.post("/v1/random", json={"min": value, "max": value})
    assert response.status_code == 200
    assert response.json()["value"] == value


INVALID_RANGES = [
    {}, {"min": 0}, {"max": 1}, {"min": 1, "max": 0},
    {"min": -2147483649, "max": 0}, {"min": 0, "max": 2147483648},
    {"min": "0", "max": 1}, {"min": 0, "max": "1"},
    {"min": 0.0, "max": 1}, {"min": 0, "max": 1.0},
    {"min": False, "max": 1}, {"min": 0, "max": True},
    {"min": None, "max": 1}, {"min": 0, "max": None},
    {"min": [], "max": 1}, {"min": 0, "max": {}},
    {"min": 0, "max": 1, "seed": 7}, {"min": 0, "max": 1, "shots": 1},
    {"min": 0, "max": 1, "attempts": 1}, {"min": 0, "max": 1, "job_kind": "random"},
]


@pytest.mark.parametrize("payload", INVALID_RANGES)
@pytest.mark.parametrize("path", ["/v1/random", "/v1/jobs/random"])
def test_random_rejects_invalid_requests(client, path, payload):
    if path.endswith("jobs/random"):
        payload = {**payload, "backend_name": "ibm_test"}
    response = client.post(path, json=payload)
    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


@pytest.mark.parametrize("path", ["/v1/random", "/v1/jobs/random"])
def test_random_requires_api_key(unauth_client, path):
    response = unauth_client.post(path, json={"min": 0, "max": 1})
    assert response.status_code == 401


def test_local_requires_qiskit_when_configured(client, monkeypatch):
    monkeypatch.setattr(runtime, "qiskit_available", False)
    monkeypatch.setattr(get_settings(), "require_qiskit", True)
    response = client.post("/v1/random", json={"min": 0, "max": 1})
    assert response.status_code == 503
    assert "REQUIRE_QISKIT=true" in response.json()["message"]


@pytest.mark.parametrize("minimum,maximum,shots", [
    (0, 0, 1), (0, 1, 1), (0, 3, 2), (0, 2, 64),
    (-2147483648, 2147483647, 32), (-2147483648, 2147483646, 1024),
])
def test_hardware_shot_budget(minimum, maximum, shots):
    assert random_job_shots(minimum, maximum) == shots


@pytest.mark.skipif(not runtime.qiskit_available, reason="Qiskit unavailable")
def test_actual_bitarray_preserves_order_and_rejects_candidates():
    from qiskit.primitives.containers import BitArray

    # Counts alone could not distinguish this from an accepted first candidate.
    bits = ["1", "1", "1", "0"] + ["0"] * 60
    result = [SimpleNamespace(data=SimpleNamespace(meas=BitArray.from_samples(bits)))]
    assert random_value_from_result(result, 0, 2) == 2


@pytest.mark.parametrize("bits", [[], ["00"], ["x"], [0], [True], ["0", "1"], "0", None])
def test_malformed_ordered_measurements(bits):
    result = [SimpleNamespace(data=SimpleNamespace(meas=SimpleNamespace(get_bitstrings=lambda: bits)))]
    with pytest.raises(RandomResultError) as error:
        random_value_from_result(result, 0, 1)
    assert error.value.reason == "malformed_provider_result"


def test_hardware_rejection_exhaustion():
    result = [SimpleNamespace(data=SimpleNamespace(meas=SimpleNamespace(get_bitstrings=lambda: ["1"] * 64)))]
    with pytest.raises(RandomResultError) as error:
        random_value_from_result(result, 0, 2)
    assert error.value.reason == "rejection_exhausted"
