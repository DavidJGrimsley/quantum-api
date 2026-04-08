from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import suppress
from typing import Any, Literal, Protocol

import numpy as np
import pennylane as qml
from pennylane.devices import Device, ExecutionConfig
from pennylane.devices.preprocess import measurements_from_counts, validate_device_wires
from pennylane.devices.qubit import measure_final_state
from pennylane.exceptions import DeviceError
from pennylane.tape import QuantumScript
from pennylane.transforms.core.compile_pipeline import CompilePipeline
from quantum_api_sdk import QuantumApiClient, QuantumApiError


class _RunQasmClient(Protocol):
    def run_qasm(self, payload: Mapping[str, Any], **kwargs: Any) -> Mapping[str, Any]:
        ...

    def close(self) -> None:
        ...


class QuantumApiDevice(Device):
    """PennyLane device backed by Quantum API /v1/qasm/run."""

    name = "Quantum API PennyLane Device"
    short_name = "quantum.api"
    pennylane_requires = ">=0.44.1"

    def __init__(
        self,
        wires: Sequence[Any] | int | None = None,
        shots: int | None = None,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        bearer_token: str | None = None,
        timeout: float = 10.0,
        qasm_version: Literal["auto", "2", "3"] = "auto",
        seed: int | None = None,
        client: _RunQasmClient | None = None,
    ) -> None:
        super().__init__(wires=wires, shots=shots)

        if qasm_version not in {"auto", "2", "3"}:
            raise ValueError("qasm_version must be one of: auto, 2, 3")

        self._qasm_version = qasm_version
        self._seed = seed

        if client is not None:
            self._client: _RunQasmClient = client
            self._owns_client = False
            return

        if not base_url:
            raise ValueError("QuantumApiDevice requires base_url when client is not provided")

        self._client = QuantumApiClient(
            base_url=base_url,
            timeout=timeout,
            api_key=api_key,
            bearer_token=bearer_token,
        )
        self._owns_client = True

    def close(self) -> None:
        if self._owns_client and hasattr(self._client, "close"):
            self._client.close()

    def __del__(self) -> None:
        with suppress(Exception):
            self.close()

    def preprocess_transforms(self, execution_config: ExecutionConfig | None = None) -> CompilePipeline:
        del execution_config

        program = CompilePipeline()
        program.add_transform(validate_device_wires, self.wires, name=self.short_name)
        # Split incompatible measurements into multiple executions before counts conversion.
        program.add_transform(qml.transforms.split_non_commuting)
        # For finite shots, convert requested measurements into a counts-compatible execution tape.
        program.add_transform(measurements_from_counts)
        return program

    def execute(
        self,
        circuits: QuantumScript | Sequence[QuantumScript],
        execution_config: ExecutionConfig | None = None,
    ) -> Any | list[Any]:
        del execution_config

        is_single_tape = isinstance(circuits, QuantumScript)
        tapes = [circuits] if is_single_tape else list(circuits)

        results = [self._execute_tape(tape) for tape in tapes]
        if is_single_tape:
            return results[0]
        return results

    def _execute_tape(self, tape: QuantumScript) -> Any:
        if tape.shots.has_partitioned_shots:
            raise DeviceError("Shot vectors are not supported by quantum.api")

        is_analytic = tape.shots.total_shots is None

        payload: dict[str, Any] = {
            "qasm": qml.to_openqasm(tape, rotations=not is_analytic, measure_all=False),
            "qasm_version": self._qasm_version,
            "shots": tape.shots.total_shots,
            "include_statevector": is_analytic,
        }
        if self._seed is not None:
            payload["seed"] = self._seed

        response = self._run_qasm(payload)

        if is_analytic:
            statevector_data = response.get("statevector")
            if not isinstance(statevector_data, list):
                raise DeviceError("Quantum API response missing statevector for analytic execution")
            statevector = _deserialize_statevector(statevector_data)
            return measure_final_state(tape, statevector, is_state_batched=False)

        raw_counts = response.get("counts")
        if not isinstance(raw_counts, dict):
            raise DeviceError("Quantum API response missing counts for shot-based execution")

        counts = _normalize_counts(raw_counts)
        results = [measurement.process_counts(counts, wire_order=tape.wires) for measurement in tape.measurements]
        return _format_results(results)

    def _run_qasm(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        try:
            return self._client.run_qasm(payload)
        except QuantumApiError as exc:
            raise DeviceError(
                f"Quantum API execution failed with status {exc.status_code}: {exc.message}"
            ) from exc
        except Exception as exc:
            raise DeviceError(f"Quantum API execution failed: {exc}") from exc


def _normalize_counts(raw_counts: Mapping[str, Any]) -> dict[str, int]:
    normalized: dict[str, int] = {}
    for key, value in raw_counts.items():
        bitstring = str(key).replace(" ", "")
        normalized[bitstring] = int(value)
    return normalized


def _deserialize_statevector(raw_statevector: Sequence[Mapping[str, Any]]) -> np.ndarray:
    amplitudes: list[complex] = []
    for amplitude in raw_statevector:
        amplitudes.append(complex(float(amplitude["real"]), float(amplitude["imag"])))
    return np.asarray(amplitudes, dtype=np.complex128)


def _format_results(results: list[Any]) -> Any:
    if len(results) == 1:
        return results[0]
    return tuple(results)
