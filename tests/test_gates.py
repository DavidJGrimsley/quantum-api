import random

from quantum_api.enums import GateType
from quantum_api.services.gate_runner import run_gate


def test_gate_runner_bit_flip_deterministic_measurement():
    result = run_gate(GateType.BIT_FLIP, rng=random.Random(1))
    assert result["measurement"] == 1
    assert result["success"] is False


def test_gate_runner_rotation_seeded_randomness():
    rng_one = random.Random(42)
    rng_two = random.Random(42)

    first = run_gate(GateType.ROTATION, rotation_angle_rad=1.2, rng=rng_one)
    second = run_gate(GateType.ROTATION, rotation_angle_rad=1.2, rng=rng_two)

    assert first == second
    assert 0.0 <= first["superposition_strength"] <= 1.0
