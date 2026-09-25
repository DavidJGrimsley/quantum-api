# Copyright (c) 2026 David J. Grimsley. All rights reserved.
from __future__ import annotations

import math

import numpy as np
import pytest

from quantum_api.main import rate_limiter, settings
from quantum_api.models.api import BraidOperation, TopologicalBraidRequest
from quantum_api.security import RateLimitResult
from quantum_api.services.topological.braid import (
    _F,
    _R,
    _dagger,
    _matmul,
    braid_generator,
    evaluate_state,
    run_topological_braid,
)


def _identity_error(matrix) -> float:
    return max(
        abs(matrix[0][0] - 1),
        abs(matrix[1][1] - 1),
        abs(matrix[0][1]),
        abs(matrix[1][0]),
    )


def test_braid_generators_are_unitary():
    for matrix in (_F, _R, braid_generator(1), braid_generator(2)):
        product = _matmul(matrix, _dagger(matrix))
        assert _identity_error(product) < 1e-12


def test_published_fibonacci_convention_is_fixed():
    phi = (1 + math.sqrt(5)) / 2
    assert _F[0][0] == pytest.approx(1 / phi, abs=1e-12)
    assert _F[0][1] == pytest.approx(1 / math.sqrt(phi), abs=1e-12)
    assert _F[1][1] == pytest.approx(-1 / phi, abs=1e-12)
    assert _R[0][0] == pytest.approx(complex(-0.8090169943749473, -0.5877852522924732), abs=1e-12)
    assert _R[1][1] == pytest.approx(complex(-0.30901699437494734, 0.9510565162951536), abs=1e-12)


def test_generator_and_inverse_cancel():
    for generator in (1, 2):
        forward = braid_generator(generator, 1)
        inverse = braid_generator(generator, -1)
        assert _identity_error(_matmul(forward, inverse)) < 1e-12


def test_three_strand_braid_relation():
    sigma1 = braid_generator(1)
    sigma2 = braid_generator(2)
    left = _matmul(_matmul(sigma1, sigma2), sigma1)
    right = _matmul(_matmul(sigma2, sigma1), sigma2)
    assert max(abs(left[i][j] - right[i][j]) for i in range(2) for j in range(2)) < 1e-12


def test_braid_order_is_non_commutative():
    sigma1 = braid_generator(1)
    sigma2 = braid_generator(2)
    first = _matmul(sigma1, sigma2)
    second = _matmul(sigma2, sigma1)
    assert max(abs(first[i][j] - second[i][j]) for i in range(2) for j in range(2)) > 1e-6


def test_empty_braid_preserves_initial_state():
    state = evaluate_state("0", [])
    assert abs(state[0] - 1) < 1e-12
    assert abs(state[1]) < 1e-12


def test_probabilities_sum_to_one_and_seeded_measurement_is_stable():
    body = {
        "braid_word": [
            {"generator": 1, "power": 1},
            {"generator": 2, "power": 1},
            {"generator": 1, "power": -1},
        ],
        "measure": True,
        "shots": 32,
        "seed": 7,
    }
    request = TopologicalBraidRequest.model_validate(body)
    first = run_topological_braid(request)
    second = run_topological_braid(request)

    probabilities = first["fusion_probabilities"]
    assert math.isclose(probabilities["vacuum"] + probabilities["tau"], 1.0, abs_tol=1e-12)
    assert first["counts"] == second["counts"]
    assert first["measurement"] == second["measurement"]


# TQSim 0.0.2 reference: one qudit, three anyons, basis indices 1 and 2
# represent fixed-total-tau logical |0> and |1>. TQSim basis index 0 is
# the total-vacuum state and must be omitted from this API's two-state sector.
@pytest.mark.parametrize(
    ("initial_state", "operations", "expected"),
    [
        (
            "0",
            [(2, 1)],
            ((-0.5, 0.3632712640026805), (-0.24293413587832285, -0.7476743906106105)),
        ),
        (
            "0",
            [(1, 1), (2, 1)],
            ((0.6180339887498949, 0.0), (-0.24293413587832305, 0.7476743906106105)),
        ),
        (
            "0",
            [(2, 1), (1, 1)],
            ((0.6180339887498949, 0.0), (0.7861513777574236, 0.0)),
        ),
        (
            "1",
            [(1, 1), (2, 1)],
            ((0.7861513777574236, 0.0), (0.1909830056250524, -0.587785252292473)),
        ),
        (
            "0",
            [
                (1, 1), (2, -1), (1, -1), (2, 1), (1, 1), (2, 1),
                (2, -1), (1, 1), (2, 1), (1, -1), (2, -1), (1, 1),
            ],
            ((0.3090169943749478, -0.22451398828979333), (-0.5432172418791008, -0.7476743906106107)),
        ),
    ],
)
def test_tqsim_reference_vectors(initial_state, operations, expected):
    request = TopologicalBraidRequest.model_validate(
        {
            "initial_state": initial_state,
            "braid_word": [{"generator": generator, "power": power} for generator, power in operations],
        }
    )
    actual = evaluate_state(request.initial_state, request.braid_word)
    for amplitude, (real, imag) in zip(actual, expected, strict=True):
        assert amplitude == pytest.approx(complex(real, imag), abs=1e-12)


def test_live_tqsim_matches_fixed_tau_sector_when_installed():
    tqsim = pytest.importorskip("tqsim", reason="TQSim is an optional test oracle")
    operations = [(1, 1), (2, -1), (1, -1), (2, 1)]
    circuit = tqsim.AnyonicCircuit(1, 3)
    assert circuit.basis == [
        {"qudits": [[1, 0]], "roots": []},
        {"qudits": [[0, 1]], "roots": []},
        {"qudits": [[1, 1]], "roots": []},
    ]
    circuit.initialize(np.array([0, 1, 0], dtype=np.complex128))
    circuit.braid_sequence([[generator, power] for generator, power in operations])
    reference = circuit.statevector().reshape(-1)
    actual = evaluate_state(
        "0",
        [BraidOperation(generator=generator, power=power) for generator, power in operations],
    )
    assert abs(reference[0]) < 1e-12
    assert np.allclose(reference[1:], actual, atol=1e-12, rtol=0)


def test_long_braid_preserves_norm_and_exact_probabilities():
    word = [{"generator": 1 if index % 2 else 2, "power": 1 if index % 3 else -1} for index in range(256)]
    result = run_topological_braid(TopologicalBraidRequest.model_validate({"braid_word": word}))
    amplitudes = [complex(value["real"], value["imag"]) for value in result["logical_state"]]
    assert sum(abs(value) ** 2 for value in amplitudes) == pytest.approx(1.0, abs=1e-12)
    assert sum(result["fusion_probabilities"].values()) == pytest.approx(1.0, abs=1e-12)


def test_measurement_defaults_to_one_shot_and_unused_shots_are_ignored():
    sampled = run_topological_braid(TopologicalBraidRequest(measure=True, seed=7))
    assert sampled["shots"] == 1
    assert sum(sampled["counts"].values()) == 1
    exact = run_topological_braid(TopologicalBraidRequest(measure=False, shots=100))
    assert exact["shots"] == 0
    assert exact["measurement"] is None
    assert exact["counts"] is None


def test_topological_braid_endpoint(client):
    response = client.post(
        "/v1/topological/braid",
        json={
            "braid_word": [
                {"generator": 1, "power": 1},
                {"generator": 2, "power": -1},
            ],
            "measure": True,
            "shots": 1,
            "seed": 11,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "fibonacci"
    assert payload["metadata"]["simulation_type"] == "digital_simulation_of_fibonacci_braid"
    assert payload["measurement"] in {"vacuum", "tau"}


def test_topological_braid_validation_rejects_unsupported_generator(client):
    response = client.post(
        "/v1/topological/braid",
        json={"braid_word": [{"generator": 3, "power": 1}]},
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {"model": "ising"},
        {"anyon_count": 4},
        {"total_charge": "vacuum"},
        {"braid_word": [{"generator": 1, "power": 2}]},
        {"braid_word": [{"generator": 1}] * 257},
        {"shots": 4097},
        {"unexpected": True},
    ],
)
def test_topological_braid_rejects_out_of_contract_payloads(client, payload):
    response = client.post("/v1/topological/braid", json=payload)
    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


def test_topological_braid_requires_api_key(unauth_client):
    response = unauth_client.post("/v1/topological/braid", json={})
    assert response.status_code == 401
    assert response.json()["error"] == "auth_required"


def test_topological_braid_requires_json_content_type(client):
    response = client.post(
        "/v1/topological/braid",
        content="{}",
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 415
    assert response.json()["request_id"] == response.headers["X-Request-ID"]


def test_topological_braid_rejects_oversized_body(client):
    response = client.post(
        "/v1/topological/braid",
        content=b" " * 65_537,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413
    assert response.json()["request_id"] == response.headers["X-Request-ID"]


def test_topological_braid_rejects_streamed_oversized_body(client):
    response = client.post(
        "/v1/topological/braid",
        content=iter((b" " * 32_768, b" " * 32_769)),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413


def test_topological_braid_respects_key_rate_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "dev_rate_limit_bypass", False)

    async def allow_ip(*, client_ip: str) -> RateLimitResult:
        return RateLimitResult(True, "ip_minute", 60, {})

    async def deny_key(*, key_id: str, policy) -> RateLimitResult:
        return RateLimitResult(False, "key_minute", 12, {"RateLimit-Remaining": "0"})

    monkeypatch.setattr(rate_limiter, "check_ip", allow_ip)
    monkeypatch.setattr(rate_limiter, "check_key", deny_key)

    response = client.post("/v1/topological/braid", json={})
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "12"
    assert response.json()["error"] == "too_many_requests"
