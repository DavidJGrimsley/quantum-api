from __future__ import annotations

import math
import random
from dataclasses import dataclass

from quantum_api.enums import GateType
from quantum_api.services.quantum_runtime import runtime


@dataclass
class QuantumGate:
    gate_type: GateType
    rotation_angle: float = 0.0

    def apply_to(self, circuit: object, qubit_index: int) -> None:
        if not runtime.qiskit_available:
            return
        if self.gate_type == GateType.BIT_FLIP:
            circuit.x(qubit_index)
        elif self.gate_type == GateType.PHASE_FLIP:
            circuit.z(qubit_index)
        elif self.gate_type == GateType.ROTATION:
            circuit.ry(self.rotation_angle, qubit_index)


class Qubit:
    """Single-qubit abstraction with qiskit-backed and math-backed execution."""

    def __init__(self) -> None:
        self._alpha = 1 + 0j
        self._beta = 0 + 0j
        self._state = runtime.Statevector([1, 0]) if runtime.qiskit_available else None

    def _sync_from_statevector(self) -> None:
        if self._state is None:
            return
        self._alpha = complex(self._state.data[0])
        self._beta = complex(self._state.data[1])

    def _apply_rotation_math(self, theta: float) -> None:
        cos_term = math.cos(theta / 2)
        sin_term = math.sin(theta / 2)
        alpha = (cos_term * self._alpha) - (sin_term * self._beta)
        beta = (sin_term * self._alpha) + (cos_term * self._beta)
        self._alpha, self._beta = alpha, beta

    def _apply_with_qiskit(self, method_name: str, theta: float | None = None) -> bool:
        if not runtime.qiskit_available or self._state is None:
            return False
        circuit = runtime.QuantumCircuit(1)
        if method_name == "x":
            circuit.x(0)
        elif method_name == "z":
            circuit.z(0)
        elif method_name == "h":
            circuit.h(0)
        elif method_name == "ry" and theta is not None:
            circuit.ry(theta, 0)
        else:
            return False
        self._state = self._state.evolve(circuit)
        self._sync_from_statevector()
        return True

    def bit_flip(self) -> None:
        if self._apply_with_qiskit("x"):
            return
        self._alpha, self._beta = self._beta, self._alpha

    def phase_flip(self) -> None:
        if self._apply_with_qiskit("z"):
            return
        self._beta = -self._beta

    def rotate_y(self, theta: float) -> None:
        if self._apply_with_qiskit("ry", theta):
            return
        self._apply_rotation_math(theta)

    def hadamard(self) -> None:
        if self._apply_with_qiskit("h"):
            return
        factor = 1 / math.sqrt(2)
        alpha = factor * (self._alpha + self._beta)
        beta = factor * (self._alpha - self._beta)
        self._alpha, self._beta = alpha, beta

    def probabilities(self) -> tuple[float, float]:
        p0 = min(max(abs(self._alpha) ** 2, 0.0), 1.0)
        p1 = min(max(abs(self._beta) ** 2, 0.0), 1.0)
        total = p0 + p1
        if total == 0:
            return 1.0, 0.0
        return p0 / total, p1 / total

    def measure(self, rng: random.Random | None = None) -> int:
        random_source = rng or random.Random()
        p0, _ = self.probabilities()
        measured = 0 if random_source.random() < p0 else 1
        if measured == 0:
            self._alpha, self._beta = 1 + 0j, 0 + 0j
            if runtime.qiskit_available:
                self._state = runtime.Statevector([1, 0])
        else:
            self._alpha, self._beta = 0 + 0j, 1 + 0j
            if runtime.qiskit_available:
                self._state = runtime.Statevector([0, 1])
        return measured

    def get_superposition_strength(self) -> float:
        return float(2 * abs(self._alpha * self._beta))


class QuantumCircuitManager:
    """Multi-qubit manager used by advanced text transformations."""

    def __init__(self, num_qubits: int) -> None:
        if num_qubits < 1 or num_qubits > 8:
            raise ValueError("num_qubits must be between 1 and 8")
        self.num_qubits = num_qubits
        self._gates: list[tuple[GateType, int, float]] = []
        self.circuit = runtime.QuantumCircuit(num_qubits) if runtime.qiskit_available else None

    def apply_gate_to_qubit(self, gate: QuantumGate, qubit_index: int) -> None:
        if not (0 <= qubit_index < self.num_qubits):
            raise ValueError("qubit index out of range")
        self._gates.append((gate.gate_type, qubit_index, gate.rotation_angle))
        if runtime.qiskit_available and self.circuit is not None:
            gate.apply_to(self.circuit, qubit_index)

    def _apply_x(self, vector: list[complex], qubit: int) -> list[complex]:
        step = 1 << qubit
        updated = vector.copy()
        for base in range(0, len(vector), step * 2):
            for offset in range(step):
                i = base + offset
                j = i + step
                updated[i], updated[j] = updated[j], updated[i]
        return updated

    def _apply_z(self, vector: list[complex], qubit: int) -> list[complex]:
        updated = vector.copy()
        for idx, value in enumerate(vector):
            if (idx >> qubit) & 1:
                updated[idx] = -value
        return updated

    def _apply_ry(self, vector: list[complex], qubit: int, theta: float) -> list[complex]:
        step = 1 << qubit
        updated = vector.copy()
        cos_term = math.cos(theta / 2)
        sin_term = math.sin(theta / 2)
        for base in range(0, len(vector), step * 2):
            for offset in range(step):
                i = base + offset
                j = i + step
                alpha = vector[i]
                beta = vector[j]
                updated[i] = (cos_term * alpha) - (sin_term * beta)
                updated[j] = (sin_term * alpha) + (cos_term * beta)
        return updated

    def _simulate_math(self) -> list[complex]:
        size = 2 ** self.num_qubits
        state = [0 + 0j] * size
        state[0] = 1 + 0j
        for gate_type, qubit_index, angle in self._gates:
            if gate_type == GateType.BIT_FLIP:
                state = self._apply_x(state, qubit_index)
            elif gate_type == GateType.PHASE_FLIP:
                state = self._apply_z(state, qubit_index)
            elif gate_type == GateType.ROTATION:
                state = self._apply_ry(state, qubit_index, angle)
        return state

    def simulate(self) -> list[complex]:
        if runtime.qiskit_available and self.circuit is not None:
            backend = runtime.AerSimulator(method="statevector")
            self.circuit.save_statevector()
            transpiled = runtime.transpile(self.circuit, backend)
            result = backend.run(transpiled, shots=1).result()
            statevector = result.get_statevector()
            raw_values = getattr(statevector, "data", statevector)
            return [complex(value) for value in raw_values]
        return self._simulate_math()
