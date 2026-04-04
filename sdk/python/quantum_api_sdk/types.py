from __future__ import annotations

from typing import Any, Literal, TypedDict

AuthMode = Literal["auto", "api_key", "bearer", "none"]
GateType = Literal["bit_flip", "phase_flip", "rotation"]
RuntimeMode = Literal["qiskit", "classical-fallback"]
BackendProvider = Literal["aer", "ibm"]
IBMChannel = Literal["ibm_quantum_platform", "ibm_cloud"]
JsonDict = dict[str, Any]


class HealthResponse(TypedDict):
    status: str
    service: str
    version: str
    qiskit_available: bool
    runtime_mode: RuntimeMode


class PortfolioMetadata(TypedDict, total=False):
    version: str
    baseUrl: str
    docsUrl: str
    healthUrl: str
    endpoints: list[dict[str, Any]]


class EchoTypeInfo(TypedDict):
    name: str
    description: str


class EchoTypesResponse(TypedDict):
    echo_types: list[EchoTypeInfo]


class GateRunRequest(TypedDict, total=False):
    gate_type: GateType
    rotation_angle_rad: float


class GateRunResponse(TypedDict):
    gate_type: GateType
    measurement: int
    superposition_strength: float
    success: bool


class CircuitOperation(TypedDict, total=False):
    gate: Literal["x", "z", "h", "ry", "cx"]
    target: int
    theta: float
    control: int


class CircuitDefinition(TypedDict):
    num_qubits: int
    operations: list[CircuitOperation]


class CircuitRunRequest(TypedDict, total=False):
    num_qubits: int
    operations: list[CircuitOperation]
    shots: int
    include_statevector: bool
    seed: int


class Amplitude(TypedDict):
    real: float
    imag: float


class CircuitRunResponse(TypedDict, total=False):
    num_qubits: int
    shots: int
    counts: dict[str, int]
    backend_mode: str
    statevector: list[Amplitude] | None


class TextTransformRequest(TypedDict):
    text: str


class TextTransformResponse(TypedDict):
    original: str
    transformed: str
    coverage_percent: float
    quantum_words: int
    total_words: int
    category_counts: dict[str, int]


class ListBackendsOptions(TypedDict, total=False):
    provider: BackendProvider
    simulator_only: bool
    min_qubits: int
    ibm_profile: str


class BackendSummary(TypedDict, total=False):
    name: str
    provider: BackendProvider
    is_simulator: bool
    is_hardware: bool
    num_qubits: int
    basis_gates: list[str]


class BackendListResponse(TypedDict, total=False):
    backends: list[BackendSummary]
    total: int
    filters_applied: JsonDict
    warnings: list[str] | None


class QasmSource(TypedDict, total=False):
    source: str
    qasm_version: Literal["auto", "2", "3"]


class TranspileRequest(TypedDict, total=False):
    circuit: CircuitDefinition
    qasm: QasmSource
    backend_name: str
    provider: BackendProvider
    ibm_profile: str
    optimization_level: int
    seed_transpiler: int
    output_qasm_version: Literal["2", "3"]


class TranspileResponse(TypedDict, total=False):
    backend_name: str
    provider: BackendProvider
    input_format: Literal["circuit", "qasm"]
    num_qubits: int
    depth: int
    size: int
    qasm: str


class QasmImportRequest(TypedDict, total=False):
    qasm: str
    qasm_version: Literal["auto", "2", "3"]


class QasmImportResponse(TypedDict, total=False):
    detected_qasm_version: Literal["2", "3"]
    num_qubits: int
    depth: int
    size: int


class QasmExportRequest(TypedDict, total=False):
    circuit: CircuitDefinition
    qasm_version: Literal["2", "3"]


class QasmExportResponse(TypedDict):
    qasm_version: Literal["2", "3"]
    qasm: str
    num_qubits: int
    depth: int
    size: int


class ApiKeyPolicyResponse(TypedDict):
    rate_limit_per_second: int
    rate_limit_per_minute: int
    daily_quota: int


class ApiKeyMetadataResponse(TypedDict, total=False):
    key_id: str
    owner_user_id: str
    name: str | None
    key_prefix: str
    masked_key: str
    status: str
    policy: ApiKeyPolicyResponse
    created_at: str
    revoked_at: str | None
    rotated_from_id: str | None
    rotated_to_id: str | None
    last_used_at: str | None


class ApiKeyListResponse(TypedDict):
    keys: list[ApiKeyMetadataResponse]


class ApiKeyCreateRequest(TypedDict, total=False):
    name: str | None


class ApiKeyCreateResponse(TypedDict):
    key: ApiKeyMetadataResponse
    raw_key: str
    secret_visible_once: bool


class ApiKeyRevokeResponse(TypedDict):
    key: ApiKeyMetadataResponse


class ApiKeyRotateResponse(TypedDict):
    previous_key: ApiKeyMetadataResponse
    new_key: ApiKeyMetadataResponse
    raw_key: str
    secret_visible_once: bool


class ApiKeyDeleteResponse(TypedDict):
    deleted_key_id: str
    deleted: bool


class ApiKeyDeleteRevokedResponse(TypedDict):
    deleted_count: int


class IBMProfileResponse(TypedDict, total=False):
    profile_id: str
    owner_user_id: str
    profile_name: str
    instance: str
    channel: IBMChannel
    masked_token: str
    is_default: bool
    verification_status: Literal["unverified", "verified", "invalid"]
    last_verified_at: str | None
    created_at: str
    updated_at: str


class IBMProfileListResponse(TypedDict):
    profiles: list[IBMProfileResponse]


class IBMProfileCreateRequest(TypedDict, total=False):
    profile_name: str
    token: str
    instance: str
    channel: IBMChannel
    is_default: bool


class IBMProfileUpdateRequest(TypedDict, total=False):
    profile_name: str
    token: str
    instance: str
    channel: IBMChannel
    is_default: bool


class IBMProfileVerifyResponse(TypedDict):
    profile: IBMProfileResponse
    verified: bool


class CircuitJobSubmitRequest(TypedDict, total=False):
    provider: Literal["ibm"]
    backend_name: str
    circuit: CircuitDefinition
    shots: int
    ibm_profile: str


class CircuitJobSubmitResponse(TypedDict, total=False):
    job_id: str
    provider: Literal["ibm"]
    backend_name: str
    ibm_profile: str | None
    remote_job_id: str | None
    status: str
    created_at: str


class CircuitJobStatusResponse(TypedDict, total=False):
    job_id: str
    provider: Literal["ibm"]
    backend_name: str
    status: str


class CircuitJobResultResponse(TypedDict):
    job_id: str
    status: str
    result: JsonDict


# Advanced domain request/response payloads currently stay schema-flexible in the
# standalone SDK so the full `/v1` surface is available without duplicating every
# server-side model definition here.
GroverSearchRequest = JsonDict
GroverSearchResponse = JsonDict
AmplitudeEstimationRequest = JsonDict
AmplitudeEstimationResponse = JsonDict
PhaseEstimationRequest = JsonDict
PhaseEstimationResponse = JsonDict
TimeEvolutionRequest = JsonDict
TimeEvolutionResponse = JsonDict

OptimizationQaoaRequest = JsonDict
OptimizationQaoaResponse = JsonDict
OptimizationVqeRequest = JsonDict
OptimizationVqeResponse = JsonDict
OptimizationMaxcutRequest = JsonDict
OptimizationMaxcutResponse = JsonDict
OptimizationKnapsackRequest = JsonDict
OptimizationKnapsackResponse = JsonDict
OptimizationTspRequest = JsonDict
OptimizationTspResponse = JsonDict

StateTomographyRequest = JsonDict
StateTomographyResponse = JsonDict
RandomizedBenchmarkingRequest = JsonDict
RandomizedBenchmarkingResponse = JsonDict
QuantumVolumeRequest = JsonDict
QuantumVolumeResponse = JsonDict
T1ExperimentRequest = JsonDict
T1ExperimentResponse = JsonDict
T2RamseyExperimentRequest = JsonDict
T2RamseyExperimentResponse = JsonDict

FinancePortfolioOptimizationRequest = JsonDict
FinancePortfolioOptimizationResponse = JsonDict
FinancePortfolioDiversificationRequest = JsonDict
FinancePortfolioDiversificationResponse = JsonDict

KernelClassifierRequest = JsonDict
KernelClassifierResponse = JsonDict
VqcClassifierRequest = JsonDict
VqcClassifierResponse = JsonDict
QsvrRegressorRequest = JsonDict
QsvrRegressorResponse = JsonDict

NatureGroundStateEnergyRequest = JsonDict
NatureGroundStateEnergyResponse = JsonDict
NatureFermionicMappingPreviewRequest = JsonDict
NatureFermionicMappingPreviewResponse = JsonDict
