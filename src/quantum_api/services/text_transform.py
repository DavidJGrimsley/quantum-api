from __future__ import annotations

import random
import re

from quantum_api.enums import EchoType, GateType
from quantum_api.services.quantum_core import QuantumCircuitManager, QuantumGate
from quantum_api.services.quantum_word_dictionary import get_quantum_category_for_word

TOKEN_SPLIT_RE = re.compile(r"\b[\w']+\b|\W+")

_GHOST_MAP = {
    "a": "ᵃ", "b": "ᵇ", "c": "ᶜ", "d": "ᵈ", "e": "ᵉ", "f": "ᶠ", "g": "ᵍ", "h": "ʰ",
    "i": "ⁱ", "j": "ʲ", "k": "ᵏ", "l": "ˡ", "m": "ᵐ", "n": "ⁿ", "o": "ᵒ", "p": "ᵖ",
    "q": "ꝗ", "r": "ʳ", "s": "ˢ", "t": "ᵗ", "u": "ᵘ", "v": "ᵛ", "w": "ʷ", "x": "ˣ",
    "y": "ʸ", "z": "ᶻ",
}

_DIACRITIC_MAP = {
    "a": "å", "b": "ƀ", "c": "ç", "d": "đ", "e": "ê", "f": "ƒ", "g": "ğ", "h": "ħ",
    "i": "ï", "j": "ĵ", "k": "ķ", "l": "ł", "m": "ɱ", "n": "ñ", "o": "ø", "p": "ƥ",
    "q": "ʠ", "r": "ř", "s": "š", "t": "ŧ", "u": "ü", "v": "ʋ", "w": "ŵ", "x": "ẋ",
    "y": "ÿ", "z": "ž",
}

_COMBINING_MARKS = ("\u0302", "\u0308", "\u0332", "\u0336")


def _preserve_case(source: str, transformed: str) -> str:
    return transformed.upper() if source.isupper() else transformed


def _map_stylized(char: str, mapping: dict[str, str]) -> str:
    mapped = mapping.get(char.lower())
    if mapped is None:
        return char
    return _preserve_case(char, mapped)


def _to_fullwidth(char: str) -> str:
    if not char.isascii():
        return char
    code = ord(char)
    if 33 <= code <= 126:
        return chr(code + 0xFEE0)
    return char


def _add_combining_mark(char: str, rng: random.Random) -> str:
    if not char.isalpha():
        return char
    return f"{char}{rng.choice(_COMBINING_MARKS)}"


def _force_visible_mutation(word: str, category: EchoType, rng: random.Random) -> str:
    alpha_positions = [index for index, char in enumerate(word) if char.isalpha()]
    if not alpha_positions:
        return word

    chars = list(word)
    if category == EchoType.QUANTUM_ENTANGLEMENT and len(alpha_positions) > 1:
        first = alpha_positions[0]
        last = alpha_positions[-1]
        chars[first] = _map_stylized(chars[first], _GHOST_MAP)
        chars[last] = _map_stylized(chars[last], _DIACRITIC_MAP)
        return "".join(chars)

    if category == EchoType.QUANTUM_GATES:
        target_index = alpha_positions[len(alpha_positions) // 2]
        chars[target_index] = _to_fullwidth(chars[target_index])
        return "".join(chars)

    target_index = alpha_positions[int(rng.random() * len(alpha_positions))]
    if category == EchoType.QUANTUM_INTERFERENCE:
        chars[target_index] = _add_combining_mark(_map_stylized(chars[target_index], _DIACRITIC_MAP), rng)
    else:
        chars[target_index] = _map_stylized(chars[target_index], _GHOST_MAP)
    return "".join(chars)


def _transform_basic(word: str, category: EchoType, rng: random.Random) -> str:
    if category == EchoType.REVERSE:
        return word[::-1]

    if category == EchoType.QUANTUM_CAPS:
        return "".join(char.upper() if rng.random() > 0.45 else char.lower() for char in word)

    if category == EchoType.GHOST:
        transformed = []
        for char in word:
            transformed.append(_map_stylized(char, _GHOST_MAP))
        return "".join(transformed)

    if category == EchoType.SCRAMBLE and len(word) > 3:
        middle = list(word[1:-1])
        rng.shuffle(middle)
        return word[0] + "".join(middle) + word[-1]

    return "".join(
        _map_stylized(char, _DIACRITIC_MAP) if char.isalpha() and rng.random() > 0.45 else char
        for char in word
    )


def _transform_from_statevector(
    word: str,
    amplitudes: list[complex],
    category: EchoType,
    rng: random.Random,
) -> str:
    output: list[str] = []
    magnitude = [abs(value) for value in amplitudes]
    alpha_total = sum(1 for char in word if char.isalpha())
    alpha_position = 0

    for char in word:
        if not char.isalpha():
            output.append(char)
            continue

        if magnitude and alpha_total > 1:
            spectrum_index = round((alpha_position / (alpha_total - 1)) * (len(magnitude) - 1))
            amp = magnitude[spectrum_index]
        elif magnitude:
            amp = magnitude[-1]
        else:
            amp = 0.0

        if category == EchoType.QUANTUM_GATES:
            if amp > 0.6:
                output.append(_to_fullwidth(char))
            elif amp > 0.22:
                output.append(_map_stylized(char, _DIACRITIC_MAP))
            elif rng.random() > 0.5:
                output.append(_add_combining_mark(char, rng))
            else:
                output.append(char)
        elif category == EchoType.QUANTUM_ENTANGLEMENT:
            if amp > 0.55:
                output.append(_map_stylized(char, _GHOST_MAP))
            elif amp > 0.25:
                output.append(_map_stylized(char, _DIACRITIC_MAP))
            elif rng.random() > 0.7:
                output.append(_to_fullwidth(char))
            else:
                output.append(char)
        else:  # QUANTUM_INTERFERENCE
            if amp > 0.6:
                output.append(_add_combining_mark(_map_stylized(char, _DIACRITIC_MAP), rng))
            elif amp > 0.25:
                output.append(_map_stylized(char, _DIACRITIC_MAP))
            elif rng.random() > 0.65:
                output.append(_map_stylized(char, _GHOST_MAP))
            else:
                output.append(char)

        alpha_position += 1

    transformed = "".join(output)
    if transformed == word:
        return _force_visible_mutation(word, category, rng)
    return transformed


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
    return _transform_from_statevector(word, statevector, category, rng)


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
