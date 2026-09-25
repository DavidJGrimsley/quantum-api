from __future__ import annotations

import math

from quantum_api.models.api import TopologicalBraidRequest
from quantum_api.services.topological.braid import (
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
    for generator in (1, 2):
        matrix = braid_generator(generator)
        product = _matmul(matrix, _dagger(matrix))
        assert _identity_error(product) < 1e-12


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
