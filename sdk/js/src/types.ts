export type AuthMode = "auto" | "apiKey" | "bearer" | "none";
export type JsonMap = Record<string, unknown>;
export type GateType = "bit_flip" | "phase_flip" | "rotation";
export type RuntimeMode = "qiskit" | "classical-fallback";
export type BackendProvider = "aer" | "ibm";
export type IBMChannel = "ibm_quantum_platform" | "ibm_cloud";

export interface QuantumApiClientOptions {
  baseUrl: string;
  apiKey?: string;
  bearerToken?: string;
  defaultAuthMode?: AuthMode;
  fetchImpl?: typeof fetch;
}

export interface RequestOptions {
  auth?: AuthMode;
  apiKey?: string;
  bearerToken?: string;
  headers?: HeadersInit;
  signal?: AbortSignal;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  qiskit_available: boolean;
  runtime_mode: RuntimeMode;
}

export interface PortfolioMetadata extends JsonMap {
  version?: string;
  baseUrl?: string;
  docsUrl?: string;
  healthUrl?: string;
  endpoints?: unknown[];
}

export interface EchoTypeInfo {
  name: string;
  description: string;
}

export interface EchoTypesResponse {
  echo_types: EchoTypeInfo[];
}

export interface GateRunRequest {
  gate_type: GateType;
  rotation_angle_rad?: number;
}

export interface GateRunResponse {
  gate_type: GateType;
  measurement: 0 | 1;
  superposition_strength: number;
  success: boolean;
}

export interface CircuitOperation {
  gate: "x" | "z" | "h" | "ry" | "cx";
  target: number;
  theta?: number;
  control?: number;
}

export interface CircuitDefinition {
  num_qubits: number;
  operations: CircuitOperation[];
}

export interface CircuitRunRequest extends CircuitDefinition {
  shots?: number;
  include_statevector?: boolean;
  seed?: number;
}

export interface Amplitude {
  real: number;
  imag: number;
}

export interface CircuitRunResponse {
  num_qubits: number;
  shots: number;
  counts: Record<string, number>;
  backend_mode: string;
  statevector?: Amplitude[] | null;
}

export interface TextTransformRequest {
  text: string;
}

export interface TextTransformResponse {
  original: string;
  transformed: string;
  coverage_percent: number;
  quantum_words: number;
  total_words: number;
  category_counts: Record<string, number>;
}

export interface ListBackendsOptions {
  provider?: BackendProvider;
  simulator_only?: boolean;
  min_qubits?: number;
  ibm_profile?: string;
}

export interface BackendSummary extends JsonMap {
  name: string;
  provider: BackendProvider;
  is_simulator: boolean;
  is_hardware: boolean;
  num_qubits: number;
  basis_gates: string[];
}

export interface BackendListResponse {
  backends: BackendSummary[];
  total: number;
  filters_applied: JsonMap;
  warnings?: string[] | null;
}

export interface QasmSource {
  source: string;
  qasm_version?: "auto" | "2" | "3";
}

export interface TranspileRequest extends JsonMap {
  circuit?: CircuitDefinition;
  qasm?: QasmSource;
  backend_name: string;
  provider?: BackendProvider;
  ibm_profile?: string;
  optimization_level?: number;
  seed_transpiler?: number;
  output_qasm_version?: "2" | "3";
}

export interface TranspileResponse extends JsonMap {
  backend_name: string;
  provider: BackendProvider;
  input_format: "circuit" | "qasm";
  num_qubits: number;
  depth: number;
  size: number;
  qasm: string;
}

export interface QasmImportRequest {
  qasm: string;
  qasm_version?: "auto" | "2" | "3";
}

export interface QasmImportResponse extends JsonMap {
  detected_qasm_version: "2" | "3";
  num_qubits: number;
  depth: number;
  size: number;
}

export interface QasmExportRequest {
  circuit: CircuitDefinition;
  qasm_version?: "2" | "3";
}

export interface QasmExportResponse {
  qasm_version: "2" | "3";
  qasm: string;
  num_qubits: number;
  depth: number;
  size: number;
}

export interface ApiKeyPolicyResponse {
  rate_limit_per_second: number;
  rate_limit_per_minute: number;
  daily_quota: number;
}

export interface ApiKeyMetadataResponse {
  key_id: string;
  owner_user_id: string;
  name?: string | null;
  key_prefix: string;
  masked_key: string;
  status: string;
  policy: ApiKeyPolicyResponse;
  created_at: string;
  revoked_at?: string | null;
  rotated_from_id?: string | null;
  rotated_to_id?: string | null;
  last_used_at?: string | null;
}

export interface ApiKeyListResponse {
  keys: ApiKeyMetadataResponse[];
}

export interface ApiKeyCreateRequest {
  name?: string | null;
}

export interface ApiKeyCreateResponse {
  key: ApiKeyMetadataResponse;
  raw_key: string;
  secret_visible_once: boolean;
}

export interface ApiKeyRevokeResponse {
  key: ApiKeyMetadataResponse;
}

export interface ApiKeyRotateResponse {
  previous_key: ApiKeyMetadataResponse;
  new_key: ApiKeyMetadataResponse;
  raw_key: string;
  secret_visible_once: boolean;
}

export interface ApiKeyDeleteResponse {
  deleted_key_id: string;
  deleted: boolean;
}

export interface ApiKeyDeleteRevokedResponse {
  deleted_count: number;
}

export interface IBMProfileResponse {
  profile_id: string;
  owner_user_id: string;
  profile_name: string;
  instance: string;
  channel: IBMChannel;
  masked_token: string;
  is_default: boolean;
  verification_status: "unverified" | "verified" | "invalid";
  last_verified_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface IBMProfileListResponse {
  profiles: IBMProfileResponse[];
}

export interface IBMProfileCreateRequest {
  profile_name: string;
  token: string;
  instance: string;
  channel?: IBMChannel;
  is_default?: boolean;
}

export interface IBMProfileUpdateRequest {
  profile_name?: string;
  token?: string;
  instance?: string;
  channel?: IBMChannel;
  is_default?: boolean;
}

export interface IBMProfileVerifyResponse {
  profile: IBMProfileResponse;
  verified: boolean;
}

export interface CircuitJobSubmitRequest extends JsonMap {
  provider?: "ibm";
  backend_name: string;
  circuit: CircuitDefinition;
  shots?: number;
  ibm_profile?: string;
}

export interface CircuitJobSubmitResponse extends JsonMap {
  job_id: string;
  provider: "ibm";
  backend_name: string;
  ibm_profile?: string | null;
  remote_job_id?: string | null;
  status: string;
  created_at: string;
}

export interface CircuitJobStatusResponse extends JsonMap {
  job_id: string;
  provider: "ibm";
  backend_name: string;
  status: string;
}

export interface CircuitJobResultResponse extends JsonMap {
  job_id: string;
  status: string;
  result: JsonMap;
}

export type GroverSearchRequest = JsonMap;
export type GroverSearchResponse = JsonMap;
export type AmplitudeEstimationRequest = JsonMap;
export type AmplitudeEstimationResponse = JsonMap;
export type PhaseEstimationRequest = JsonMap;
export type PhaseEstimationResponse = JsonMap;
export type TimeEvolutionRequest = JsonMap;
export type TimeEvolutionResponse = JsonMap;
export type OptimizationQaoaRequest = JsonMap;
export type OptimizationQaoaResponse = JsonMap;
export type OptimizationVqeRequest = JsonMap;
export type OptimizationVqeResponse = JsonMap;
export type OptimizationMaxcutRequest = JsonMap;
export type OptimizationMaxcutResponse = JsonMap;
export type OptimizationKnapsackRequest = JsonMap;
export type OptimizationKnapsackResponse = JsonMap;
export type OptimizationTspRequest = JsonMap;
export type OptimizationTspResponse = JsonMap;
export type StateTomographyRequest = JsonMap;
export type StateTomographyResponse = JsonMap;
export type RandomizedBenchmarkingRequest = JsonMap;
export type RandomizedBenchmarkingResponse = JsonMap;
export type QuantumVolumeRequest = JsonMap;
export type QuantumVolumeResponse = JsonMap;
export type T1ExperimentRequest = JsonMap;
export type T1ExperimentResponse = JsonMap;
export type T2RamseyExperimentRequest = JsonMap;
export type T2RamseyExperimentResponse = JsonMap;
export type FinancePortfolioOptimizationRequest = JsonMap;
export type FinancePortfolioOptimizationResponse = JsonMap;
export type FinancePortfolioDiversificationRequest = JsonMap;
export type FinancePortfolioDiversificationResponse = JsonMap;
export type KernelClassifierRequest = JsonMap;
export type KernelClassifierResponse = JsonMap;
export type VqcClassifierRequest = JsonMap;
export type VqcClassifierResponse = JsonMap;
export type QsvrRegressorRequest = JsonMap;
export type QsvrRegressorResponse = JsonMap;
export type NatureGroundStateEnergyRequest = JsonMap;
export type NatureGroundStateEnergyResponse = JsonMap;
export type NatureFermionicMappingPreviewRequest = JsonMap;
export type NatureFermionicMappingPreviewResponse = JsonMap;
