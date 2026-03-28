from __future__ import annotations

import random
import re

from quantum_api.enums import EchoType, GateType
from quantum_api.services.quantum_core import QuantumCircuitManager, QuantumGate
from quantum_api.services.quantum_word_dictionary import get_quantum_category_for_word

TOKEN_SPLIT_RE = re.compile(r"\b[\w']+\b|\W+")

_GHOST_MAP = {
    "a": "a^", "e": "e^", "i": "i^", "o": "o^", "u": "u^", "n": "n~", "s": "s~",
}

_DIACRITIC_MAP = {
    "a": "a-", "e": "e-", "i": "i-", "o": "o-", "u": "u-", "n": "n~", "s": "s~",
}


def _transform_basic(word: str, category: EchoType, rng: random.Random) -> str:
    if category == EchoType.REVERSE:
        return word[::-1]

    if category == EchoType.QUANTUM_CAPS:
        return "".join(char.upper() if rng.random() > 0.45 else char.lower() for char in word)

    if category == EchoType.GHOST:
        transformed = []
        for char in word:
            mapped = _GHOST_MAP.get(char.lower())
            transformed.append(mapped if mapped else char)
        return "".join(transformed)

    if category == EchoType.SCRAMBLE and len(word) > 3:
        middle = list(word[1:-1])
        rng.shuffle(middle)
        return word[0] + "".join(middle) + word[-1]

    return "".join(_DIACRITIC_MAP.get(char.lower(), char) if rng.random() > 0.65 else char for char in word)


def _transform_from_statevector(word: str, amplitudes: list[complex], rng: random.Random) -> str:
    output: list[str] = []
    magnitude = [abs(value) for value in amplitudes]
    for index, char in enumerate(word):
        if not char.isalpha():
            output.append(char)
            continue
        amp = magnitude[index % len(magnitude)] if magnitude else 0.0
        if amp > 0.75:
            output.append(char.upper())
        elif amp > 0.45:
            output.append(char.swapcase())
        elif amp > 0.2 and rng.random() > 0.5:
            output.append(_DIACRITIC_MAP.get(char.lower(), char))
        else:
            output.append(char)
    return "".join(output)


def _transform_advanced(word: str, category: EchoType, rng: random.Random) -> str:
    qubits = min(max(len(word), 1), 8)
    manager = QuantumCircuitManager(qubits)

    if category == EchoType.QUANTUM_GATES:
        for index in range(qubits):
            gate = QuantumGate(GateType.BIT_FLIP if index % 2 == 0 else GateType.PHASE_FLIP)
            manager.apply_gate_to_qubit(gate, index)
    elif category == EchoType.QUANTUM_ENTANGLEMENT:
        for index in range(0, qubits, 2):
            manager.apply_gate_to_qubit(QuantumGate(GateType.BIT_FLIP), index)
        for index in range(1, qubits, 2):
            manager.apply_gate_to_qubit(QuantumGate(GateType.ROTATION, rotation_angle=0.35), index)
    else:  # QUANTUM_INTERFERENCE
        for index in range(qubits):
            manager.apply_gate_to_qubit(QuantumGate(GateType.ROTATION, rotation_angle=0.2 + (0.05 * index)), index)
            if rng.random() > 0.5:
                manager.apply_gate_to_qubit(QuantumGate(GateType.PHASE_FLIP), index)

    statevector = manager.simulate()
    return _transform_from_statevector(word, statevector, rng)


def transform_text(text: str, rng: random.Random | None = None) -> dict[str, object]:
    random_source = rng or random.Random()
    tokens = TOKEN_SPLIT_RE.findall(text)

    transformed_tokens: list[str] = []
    category_counts: dict[str, int] = {echo_type.value: 0 for echo_type in EchoType}

    total_words = 0
    quantum_words = 0

    for token in tokens:
        if token.isalpha() or ("'" in token and token.replace("'", "").isalpha()):
            total_words += 1
            category = get_quantum_category_for_word(token)
            category_counts[category.value] += 1

            if category == EchoType.ORIGINAL:
                transformed_tokens.append(token)
                continue

            quantum_words += 1
            if category in {
                EchoType.SCRAMBLE,
                EchoType.REVERSE,
                EchoType.GHOST,
                EchoType.QUANTUM_CAPS,
            }:
                transformed_tokens.append(_transform_basic(token, category, random_source))
            else:
                transformed_tokens.append(_transform_advanced(token, category, random_source))
        else:
            transformed_tokens.append(token)

    coverage_percent = (quantum_words / total_words * 100) if total_words else 0.0

    return {
        "original": text,
        "transformed": "".join(transformed_tokens),
        "coverage_percent": round(coverage_percent, 2),
        "quantum_words": quantum_words,
        "total_words": total_words,
        "category_counts": category_counts,
    }
