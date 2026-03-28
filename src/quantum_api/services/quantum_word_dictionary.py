from __future__ import annotations

import re

from quantum_api.enums import EchoType

QUANTUM_INTERFERENCE_WORDS = {
    "memory", "remember", "remembered", "forgotten", "fragment", "fragments", "echo",
    "echoes", "collapse", "uncertainty", "timeline", "resonance", "anomaly", "signal",
    "pulse", "decoherence", "flicker", "archive", "imprint", "trace", "interference",
}

QUANTUM_GATES_WORDS = {
    "quantum", "gate", "gates", "circuit", "circuits", "qubit", "qubits", "phase",
    "rotation", "entangler", "statevector", "simulator", "hamiltonian", "operator",
    "control", "oracle", "transpile", "measurement", "basis", "unitary",
}

QUANTUM_ENTANGLEMENT_WORDS = {
    "entangled", "entanglement", "bond", "linked", "pair", "pairs", "correlated",
    "together", "synced", "mirror", "duality", "connection", "connected", "coupled",
    "parallel", "branch", "branches", "superposed", "cohere", "coherence",
}

GHOST_WORDS = {
    "whisper", "whispers", "ghost", "ghostly", "specter", "spectral", "veil", "mist",
    "phantom", "hush", "haunt", "haunted", "ether", "hollow", "shade", "faded",
}

QUANTUM_CAPS_WORDS = {
    "alert", "warning", "critical", "system", "override", "core", "reactor", "engine",
    "uplink", "stability", "diagnostic", "lock", "locked", "unlock", "firewall", "auth",
}

SCRAMBLE_WORDS = {
    "chaos", "random", "shift", "drift", "scatter", "fragmented", "distort", "noise",
    "glitch", "anomalous", "warped", "unstable", "unknown", "maze", "puzzle", "twist",
}

REVERSE_WORDS = {
    "return", "reflect", "reverse", "rewind", "again", "back", "retreat", "fallback",
    "mirror", "invert", "undo", "restore", "retrace", "replay", "decode", "rebuild",
}

TOKEN_PATTERN = re.compile(r"\b[\w']+\b")


def get_quantum_category_for_word(word: str) -> EchoType:
    token = word.lower().strip()
    if token in QUANTUM_INTERFERENCE_WORDS:
        return EchoType.QUANTUM_INTERFERENCE
    if token in QUANTUM_GATES_WORDS:
        return EchoType.QUANTUM_GATES
    if token in QUANTUM_ENTANGLEMENT_WORDS:
        return EchoType.QUANTUM_ENTANGLEMENT
    if token in GHOST_WORDS:
        return EchoType.GHOST
    if token in QUANTUM_CAPS_WORDS:
        return EchoType.QUANTUM_CAPS
    if token in SCRAMBLE_WORDS:
        return EchoType.SCRAMBLE
    if token in REVERSE_WORDS:
        return EchoType.REVERSE
    return EchoType.ORIGINAL


def analyze_text_coverage(text: str) -> dict[str, float | int | dict[str, int]]:
    words = TOKEN_PATTERN.findall(text)
    category_counts: dict[str, int] = {echo_type.value: 0 for echo_type in EchoType}

    total_words = 0
    quantum_words = 0
    for word in words:
        if not word:
            continue
        total_words += 1
        category = get_quantum_category_for_word(word)
        category_counts[category.value] += 1
        if category != EchoType.ORIGINAL:
            quantum_words += 1

    coverage_percent = (quantum_words / total_words * 100) if total_words else 0.0
    return {
        "total_words": total_words,
        "quantum_words": quantum_words,
        "coverage_percent": round(coverage_percent, 2),
        "category_counts": category_counts,
    }
