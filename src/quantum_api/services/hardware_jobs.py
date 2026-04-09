from __future__ import annotations

from typing import Any

from quantum_api.execution_jobs import ExecutionJobRecord, QuantumExecutionJobService
from quantum_api.ibm_credentials import ResolvedIbmCredentials
from quantum_api.models.api import CircuitJobSubmitRequest, QasmJobSubmitRequest
from quantum_api.services.backend_catalog import ensure_backend_supports_qubits, resolve_backend
from quantum_api.services.circuit_conversion import build_circuit_from_definition, parse_qasm
from quantum_api.services.ibm_provider import (
    build_ibm_service,
    normalize_runtime_job_status,
    runtime_job_error_payload,
)
from quantum_api.services.quantum_runtime import runtime
from quantum_api.services.service_errors import ProviderUnavailableError, ResultNotReadyError


def _remote_job_id(job: Any) -> str:
    for attribute in ("job_id",):
        value = getattr(job, attribute, None)
        if callable(value):
            try:
                value = value()
            except Exception:
                value = None
        if value:
            return str(value)
    return "unknown_remote_job"


def _measurement_counts_from_result(raw_result: Any, num_qubits: int) -> dict[str, int]:
    counts_source = None

    if hasattr(raw_result, "__getitem__"):
        try:
            first = raw_result[0]
        except Exception:
            first = None
        if first is not None:
            data = getattr(first, "data", None)
            if data is not None:
                for attribute in ("meas", "c", "cr"):
                    register = getattr(data, attribute, None)
                    if register is not None and hasattr(register, "get_counts"):
                        counts_source = register.get_counts()
                        break

    if counts_source is None and hasattr(raw_result, "get_counts"):
        counts_source = raw_result.get_counts()

    if not isinstance(counts_source, dict):
        raise RuntimeError("Unable to extract measurement counts from IBM Sampler result.")

    normalized_counts = {str(key).zfill(num_qubits): int(value) for key, value in counts_source.items()}
    return dict(sorted(normalized_counts.items()))


class HardwareJobService:
    def __init__(self, job_service: QuantumExecutionJobService) -> None:
        self._job_service = job_service

    async def submit_circuit_job(
        self,
        *,
        owner_user_id: str,
        api_key_id: str,
        request_data: CircuitJobSubmitRequest,
        ibm_credentials: ResolvedIbmCredentials,
    ) -> ExecutionJobRecord:
        if request_data.provider != "ibm":
            raise ProviderUnavailableError(
                provider=request_data.provider,
                details={"reason": "unsupported_provider"},
            )
        if runtime.transpile is None or runtime.SamplerV2 is None:
            raise ProviderUnavailableError(
                provider="ibm",
                details={
                    "reason": "missing_dependency",
                    "message": "Install qiskit-ibm-runtime to submit IBM hardware jobs.",
                    "import_error": runtime.ibm_runtime_import_error,
                },
            )

        provider, backend = resolve_backend(
            request_data.backend_name,
            "ibm",
            ibm_credentials=ibm_credentials,
        )
        circuit = build_circuit_from_definition(request_data.circuit)
        ensure_backend_supports_qubits(
            backend_name=request_data.backend_name,
            provider=provider,
            backend=backend,
            required_qubits=int(circuit.num_qubits),
        )
        measured_circuit = circuit.copy()
        measured_circuit.measure_all()
        transpiled = runtime.transpile(measured_circuit, backend)

        sampler = runtime.SamplerV2(mode=backend)
        remote_job = sampler.run([transpiled], shots=request_data.shots)
        status = normalize_runtime_job_status(remote_job.status())

        return await self._job_service.create_job(
            owner_user_id=owner_user_id,
            api_key_id=api_key_id,
            provider=request_data.provider,
            backend_name=request_data.backend_name,
            ibm_profile_name=ibm_credentials.profile_name,
            credential_instance=ibm_credentials.instance,
            credential_channel=ibm_credentials.channel,
            credential_masked_token=ibm_credentials.masked_token,
            credential_token_ciphertext=ibm_credentials.token_ciphertext,
            remote_job_id=_remote_job_id(remote_job),
            status=status,
            request_payload=request_data.model_dump(mode="json"),
        )

    async def submit_qasm_job(
        self,
        *,
        owner_user_id: str,
        api_key_id: str,
        request_data: QasmJobSubmitRequest,
        ibm_credentials: ResolvedIbmCredentials,
    ) -> ExecutionJobRecord:
        if request_data.provider != "ibm":
            raise ProviderUnavailableError(
                provider=request_data.provider,
                details={"reason": "unsupported_provider"},
            )
        if runtime.transpile is None or runtime.SamplerV2 is None:
            raise ProviderUnavailableError(
                provider="ibm",
                details={
                    "reason": "missing_dependency",
                    "message": "Install qiskit-ibm-runtime to submit IBM hardware jobs.",
                    "import_error": runtime.ibm_runtime_import_error,
                },
            )

        provider, backend = resolve_backend(
            request_data.backend_name,
            "ibm",
            ibm_credentials=ibm_credentials,
        )
        circuit, detected_qasm_version = parse_qasm(
            source=request_data.qasm,
            qasm_version=request_data.qasm_version,
        )
        ensure_backend_supports_qubits(
            backend_name=request_data.backend_name,
            provider=provider,
            backend=backend,
            required_qubits=int(circuit.num_qubits),
        )
        measured_circuit = circuit.copy()
        has_measurements = any(
            str(instruction.operation.name) == "measure"
            for instruction in measured_circuit.data
        )
        if not has_measurements:
            measured_circuit.measure_all()
        transpiled = runtime.transpile(measured_circuit, backend)

        sampler = runtime.SamplerV2(mode=backend)
        remote_job = sampler.run([transpiled], shots=request_data.shots)
        status = normalize_runtime_job_status(remote_job.status())
        request_payload = request_data.model_dump(mode="json")
        request_payload["detected_qasm_version"] = detected_qasm_version
        request_payload["num_qubits"] = int(circuit.num_qubits)

        return await self._job_service.create_job(
            owner_user_id=owner_user_id,
            api_key_id=api_key_id,
            provider=request_data.provider,
            backend_name=request_data.backend_name,
            ibm_profile_name=ibm_credentials.profile_name,
            credential_instance=ibm_credentials.instance,
            credential_channel=ibm_credentials.channel,
            credential_masked_token=ibm_credentials.masked_token,
            credential_token_ciphertext=ibm_credentials.token_ciphertext,
            remote_job_id=_remote_job_id(remote_job),
            status=status,
            request_payload=request_payload,
        )

    async def refresh_job(self, *, record: ExecutionJobRecord, decrypted_token: str) -> ExecutionJobRecord:
        if record.status in {"succeeded", "failed", "cancelled"}:
            return record

        credentials = ResolvedIbmCredentials(
            owner_user_id=record.owner_user_id,
            profile_id=None,
            profile_name=record.ibm_profile_name,
            instance=record.credential_instance,
            channel=record.credential_channel,
            masked_token=record.credential_masked_token,
            token=decrypted_token,
            token_ciphertext=record.credential_token_ciphertext,
            source="job_snapshot",
        )
        service = build_ibm_service(credentials)
        remote_job = service.job(record.remote_job_id)
        status = normalize_runtime_job_status(remote_job.status())

        if status == "succeeded":
            num_qubits_value = record.request_payload.get("num_qubits")
            if num_qubits_value is None:
                num_qubits_value = record.request_payload["circuit"]["num_qubits"]
            num_qubits = int(num_qubits_value)
            shots = int(record.request_payload["shots"])
            counts = _measurement_counts_from_result(remote_job.result(), num_qubits)
            return await self._job_service.update_job(
                owner_user_id=record.owner_user_id,
                job_id=record.job_id,
                status="succeeded",
                result_payload={
                    "num_qubits": num_qubits,
                    "shots": shots,
                    "counts": counts,
                },
                error_payload=None,
            )

        if status in {"failed", "cancelled"}:
            return await self._job_service.update_job(
                owner_user_id=record.owner_user_id,
                job_id=record.job_id,
                status=status,
                error_payload=runtime_job_error_payload(remote_job),
            )

        return await self._job_service.update_job(
            owner_user_id=record.owner_user_id,
            job_id=record.job_id,
            status=status,
            result_payload=record.result_payload,
            error_payload=record.error_payload,
        )

    async def cancel_job(self, *, record: ExecutionJobRecord, decrypted_token: str) -> ExecutionJobRecord:
        if record.status in {"succeeded", "failed", "cancelled"}:
            return record

        credentials = ResolvedIbmCredentials(
            owner_user_id=record.owner_user_id,
            profile_id=None,
            profile_name=record.ibm_profile_name,
            instance=record.credential_instance,
            channel=record.credential_channel,
            masked_token=record.credential_masked_token,
            token=decrypted_token,
            token_ciphertext=record.credential_token_ciphertext,
            source="job_snapshot",
        )
        service = build_ibm_service(credentials)
        remote_job = service.job(record.remote_job_id)
        remote_job.cancel()
        updated = await self._job_service.update_job(
            owner_user_id=record.owner_user_id,
            job_id=record.job_id,
            status="cancelling",
            result_payload=record.result_payload,
            error_payload=record.error_payload,
        )
        return await self.refresh_job(record=updated, decrypted_token=decrypted_token)

    @staticmethod
    def assert_result_ready(record: ExecutionJobRecord) -> dict[str, Any]:
        if record.status != "succeeded" or record.result_payload is None:
            raise ResultNotReadyError(job_id=record.job_id, status=record.status)
        return record.result_payload
