from enum import StrEnum


class GateType(StrEnum):
    BIT_FLIP = "bit_flip"
    PHASE_FLIP = "phase_flip"
    ROTATION = "rotation"


class EchoType(StrEnum):
    SCRAMBLE = "scramble"
    REVERSE = "reverse"
    GHOST = "ghost"
    QUANTUM_CAPS = "quantum_caps"
    QUANTUM_GATES = "quantum_gates"
    QUANTUM_ENTANGLEMENT = "quantum_entanglement"
    QUANTUM_INTERFERENCE = "quantum_interference"
    ORIGINAL = "original"


ECHO_TYPE_DESCRIPTIONS: dict[EchoType, str] = {
    EchoType.SCRAMBLE: "Character scrambling influenced by quantum-style randomness.",
    EchoType.REVERSE: "Reversal-style text transformation with case perturbation.",
    EchoType.GHOST: "Ghosted superscript and spectral character rendering.",
    EchoType.QUANTUM_CAPS: "Probabilistic capitalization driven by simulated measurement.",
    EchoType.QUANTUM_GATES: "Gate-sequence inspired transformation using multi-qubit amplitudes.",
    EchoType.QUANTUM_ENTANGLEMENT: "Paired-word correlation effects and mirrored transforms.",
    EchoType.QUANTUM_INTERFERENCE: "Memory/interference-inspired mixed transformation behavior.",
    EchoType.ORIGINAL: "No transformation applied.",
}
