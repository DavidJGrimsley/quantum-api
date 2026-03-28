from __future__ import annotations

import random

from quantum_api.enums import GateType
from quantum_api.services.quantum_core import Qubit


def run_gate(
    gate_type: GateType,
    rotation_angle_rad: float | None = None,
    rng: random.Random | None = None,
) -> dict[str, float | int | bool | str]:
    qubit = Qubit()

    if gate_type == GateType.BIT_FLIP:
        qubit.bit_flip()
    elif gate_type == GateType.PHASE_FLIP:
        qubit.phase_flip()
    elif gate_type == GateType.ROTATION:
        if rotation_angle_rad is None:
            raise ValueError("rotation_angle_rad is required for rotation gate")
        qubit.rotate_y(rotation_angle_rad)

    superposition_strength = round(qubit.get_superposition_strength(), 6)
    measurement = qubit.measure(rng=rng)
    success = measurement == 0

    return {
        "gate_type": gate_type.value,
        "measurement": measurement,
        "superposition_strength": superposition_strength,
        "success": success,
    }
