from dataclasses import dataclass
from typing import Literal

GateType = Literal["bit_flip", "phase_flip", "rotation"]


@dataclass
class GateRunResponse:
    gate_type: GateType
    measurement: int
    superposition_strength: float
    success: bool


@dataclass
class TextTransformResponse:
    original: str
    transformed: str
    coverage_percent: float
    quantum_words: int
    total_words: int
    category_counts: dict[str, int]
