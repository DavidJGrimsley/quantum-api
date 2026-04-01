import random

from quantum_api.services.text_transform import transform_text


def test_text_transform_is_deterministic_with_seed():
    source = "memory fragments and quantum signals drift through the chamber"

    first = transform_text(source, rng=random.Random(7))
    second = transform_text(source, rng=random.Random(7))

    assert first["transformed"] == second["transformed"]
    assert first["category_counts"] == second["category_counts"]


def test_text_transform_reports_category_counts():
    source = "memory quantum entangled whisper warning return"
    payload = transform_text(source, rng=random.Random(11))

    assert payload["total_words"] == 6
    assert payload["quantum_words"] >= 5
    assert payload["category_counts"]["quantum_interference"] >= 1
    assert payload["category_counts"]["quantum_gates"] >= 1
    assert payload["category_counts"]["quantum_entanglement"] >= 1


def test_quantum_gates_words_are_visibly_transformed():
    source = "Hello quantum world"
    payload = transform_text(source, rng=random.Random(5))

    assert payload["category_counts"]["quantum_gates"] >= 1
    assert payload["transformed"] != source
