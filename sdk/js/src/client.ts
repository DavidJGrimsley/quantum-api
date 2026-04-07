import { QuantumApiError } from "./errors.js";
import type {
  AmplitudeEstimationRequest,
  AmplitudeEstimationResponse,
  ApiKeyCreateRequest,
  ApiKeyCreateResponse,
  ApiKeyDeleteResponse,
  ApiKeyDeleteRevokedResponse,
  ApiKeyListResponse,
  ApiKeyRevokeResponse,
  ApiKeyRotateResponse,
  AuthMode,
  BackendListResponse,
  CircuitJobResultResponse,
  CircuitJobStatusResponse,
  CircuitJobSubmitRequest,
  CircuitJobSubmitResponse,
  CircuitRunRequest,
  CircuitRunResponse,
  EchoTypesResponse,
  FinancePortfolioDiversificationRequest,
  FinancePortfolioDiversificationResponse,
  FinancePortfolioOptimizationRequest,
  FinancePortfolioOptimizationResponse,
  GateRunRequest,
  GateRunResponse,
  GroverSearchRequest,
  GroverSearchResponse,
  HealthResponse,
  IBMProfileCreateRequest,
  IBMProfileListResponse,
  IBMProfileResponse,
  IBMProfileUpdateRequest,
  IBMProfileVerifyResponse,
  KernelClassifierRequest,
  KernelClassifierResponse,
  ListBackendsOptions,
  NatureFermionicMappingPreviewRequest,
  NatureFermionicMappingPreviewResponse,
  NatureGroundStateEnergyRequest,
  NatureGroundStateEnergyResponse,
  OptimizationKnapsackRequest,
  OptimizationKnapsackResponse,
  OptimizationMaxcutRequest,
  OptimizationMaxcutResponse,
  OptimizationQaoaRequest,
  OptimizationQaoaResponse,
  OptimizationTspRequest,
  OptimizationTspResponse,
  OptimizationVqeRequest,
  OptimizationVqeResponse,
  PhaseEstimationRequest,
  PhaseEstimationResponse,
  PortfolioMetadata,
  QasmExportRequest,
  QasmExportResponse,
  QasmImportRequest,
  QasmImportResponse,
  QuantumApiClientOptions,
  QuantumVolumeRequest,
  QuantumVolumeResponse,
  QsvrRegressorRequest,
  QsvrRegressorResponse,
  RandomizedBenchmarkingRequest,
  RandomizedBenchmarkingResponse,
  RequestOptions,
  StateTomographyRequest,
  StateTomographyResponse,
  T1ExperimentRequest,
  T1ExperimentResponse,
  T2RamseyExperimentRequest,
  T2RamseyExperimentResponse,
  TextTransformRequest,
  TextTransformResponse,
  TimeEvolutionRequest,
  TimeEvolutionResponse,
  TranspileRequest,
  TranspileResponse,
  VqcClassifierRequest,
  VqcClassifierResponse,
} from "./types.js";

interface RequestJsonOptions extends RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined>;
}

export class QuantumApiClient {
  private readonly baseUrl: string;
  private readonly apiKey?: string;
  private readonly bearerToken?: string;
  private readonly defaultAuthMode: AuthMode;
  private readonly fetchImpl: typeof fetch;

  constructor(options: QuantumApiClientOptions) {
    this.baseUrl = normalizeBaseUrl(options.baseUrl);
    this.apiKey = options.apiKey;
    this.bearerToken = options.bearerToken;
    this.defaultAuthMode = options.defaultAuthMode ?? "auto";
    this.fetchImpl = options.fetchImpl ?? resolveDefaultFetchImpl();
  }

  health(options?: RequestOptions): Promise<HealthResponse> {
    return this.requestJson("/health", { ...options, auth: options?.auth ?? "none" });
  }

  portfolio(options?: RequestOptions): Promise<PortfolioMetadata> {
    return this.requestJson("/portfolio.json", { ...options, auth: options?.auth ?? "none" });
  }

  echoTypes(options?: RequestOptions): Promise<EchoTypesResponse> {
    return this.requestJson("/echo-types", options);
  }

  runGate(payload: GateRunRequest, options?: RequestOptions): Promise<GateRunResponse> {
    return this.requestJson("/gates/run", { ...options, method: "POST", body: payload });
  }

  runCircuit(payload: CircuitRunRequest, options?: RequestOptions): Promise<CircuitRunResponse> {
    return this.requestJson("/circuits/run", { ...options, method: "POST", body: payload });
  }

  transformText(payload: TextTransformRequest, options?: RequestOptions): Promise<TextTransformResponse> {
    return this.requestJson("/text/transform", { ...options, method: "POST", body: payload });
  }

  listBackends(query?: ListBackendsOptions, options?: RequestOptions): Promise<BackendListResponse> {
    return this.requestJson("/list_backends", {
      ...options,
      query: query as Record<string, string | number | boolean | undefined> | undefined,
    });
  }

  transpile(payload: TranspileRequest, options?: RequestOptions): Promise<TranspileResponse> {
    return this.requestJson("/transpile", { ...options, method: "POST", body: payload });
  }

  importQasm(payload: QasmImportRequest, options?: RequestOptions): Promise<QasmImportResponse> {
    return this.requestJson("/qasm/import", { ...options, method: "POST", body: payload });
  }

  exportQasm(payload: QasmExportRequest, options?: RequestOptions): Promise<QasmExportResponse> {
    return this.requestJson("/qasm/export", { ...options, method: "POST", body: payload });
  }

  listKeys(options?: RequestOptions): Promise<ApiKeyListResponse> {
    return this.requestJson("/keys", { ...options, auth: options?.auth ?? "bearer" });
  }

  createKey(payload: ApiKeyCreateRequest, options?: RequestOptions): Promise<ApiKeyCreateResponse> {
    return this.requestJson("/keys", { ...options, auth: options?.auth ?? "bearer", method: "POST", body: payload });
  }

  revokeKey(keyId: string, options?: RequestOptions): Promise<ApiKeyRevokeResponse> {
    return this.requestJson(`/keys/${encodeURIComponent(keyId)}/revoke`, {
      ...options,
      auth: options?.auth ?? "bearer",
      method: "POST",
    });
  }

  rotateKey(keyId: string, options?: RequestOptions): Promise<ApiKeyRotateResponse> {
    return this.requestJson(`/keys/${encodeURIComponent(keyId)}/rotate`, {
      ...options,
      auth: options?.auth ?? "bearer",
      method: "POST",
    });
  }

  deleteRevokedKeys(options?: RequestOptions): Promise<ApiKeyDeleteRevokedResponse> {
    return this.requestJson("/keys/revoked", { ...options, auth: options?.auth ?? "bearer", method: "DELETE" });
  }

  deleteKey(keyId: string, options?: RequestOptions): Promise<ApiKeyDeleteResponse> {
    return this.requestJson(`/keys/${encodeURIComponent(keyId)}`, {
      ...options,
      auth: options?.auth ?? "bearer",
      method: "DELETE",
    });
  }

  listIbmProfiles(options?: RequestOptions): Promise<IBMProfileListResponse> {
    return this.requestJson("/ibm/profiles", { ...options, auth: options?.auth ?? "bearer" });
  }

  createIbmProfile(payload: IBMProfileCreateRequest, options?: RequestOptions): Promise<IBMProfileResponse> {
    return this.requestJson("/ibm/profiles", {
      ...options,
      auth: options?.auth ?? "bearer",
      method: "POST",
      body: payload,
    });
  }

  updateIbmProfile(
    profileId: string,
    payload: IBMProfileUpdateRequest,
    options?: RequestOptions,
  ): Promise<IBMProfileResponse> {
    return this.requestJson(`/ibm/profiles/${encodeURIComponent(profileId)}`, {
      ...options,
      auth: options?.auth ?? "bearer",
      method: "PATCH",
      body: payload,
    });
  }

  deleteIbmProfile(profileId: string, options?: RequestOptions): Promise<Record<string, unknown>> {
    return this.requestJson(`/ibm/profiles/${encodeURIComponent(profileId)}`, {
      ...options,
      auth: options?.auth ?? "bearer",
      method: "DELETE",
    });
  }

  verifyIbmProfile(profileId: string, options?: RequestOptions): Promise<IBMProfileVerifyResponse> {
    return this.requestJson(`/ibm/profiles/${encodeURIComponent(profileId)}/verify`, {
      ...options,
      auth: options?.auth ?? "bearer",
      method: "POST",
    });
  }

  submitCircuitJob(payload: CircuitJobSubmitRequest, options?: RequestOptions): Promise<CircuitJobSubmitResponse> {
    return this.requestJson("/jobs/circuits", { ...options, method: "POST", body: payload });
  }

  getCircuitJob(jobId: string, options?: RequestOptions): Promise<CircuitJobStatusResponse> {
    return this.requestJson(`/jobs/${encodeURIComponent(jobId)}`, options);
  }

  getCircuitJobResult(jobId: string, options?: RequestOptions): Promise<CircuitJobResultResponse> {
    return this.requestJson(`/jobs/${encodeURIComponent(jobId)}/result`, options);
  }

  cancelCircuitJob(jobId: string, options?: RequestOptions): Promise<CircuitJobStatusResponse> {
    return this.requestJson(`/jobs/${encodeURIComponent(jobId)}/cancel`, {
      ...options,
      method: "POST",
    });
  }

  groverSearch(payload: GroverSearchRequest, options?: RequestOptions): Promise<GroverSearchResponse> {
    return this.requestJson("/algorithms/grover_search", { ...options, method: "POST", body: payload });
  }

  amplitudeEstimation(
    payload: AmplitudeEstimationRequest,
    options?: RequestOptions,
  ): Promise<AmplitudeEstimationResponse> {
    return this.requestJson("/algorithms/amplitude_estimation", { ...options, method: "POST", body: payload });
  }

  phaseEstimation(payload: PhaseEstimationRequest, options?: RequestOptions): Promise<PhaseEstimationResponse> {
    return this.requestJson("/algorithms/phase_estimation", { ...options, method: "POST", body: payload });
  }

  timeEvolution(payload: TimeEvolutionRequest, options?: RequestOptions): Promise<TimeEvolutionResponse> {
    return this.requestJson("/algorithms/time_evolution", { ...options, method: "POST", body: payload });
  }

  qaoa(payload: OptimizationQaoaRequest, options?: RequestOptions): Promise<OptimizationQaoaResponse> {
    return this.requestJson("/optimization/qaoa", { ...options, method: "POST", body: payload });
  }

  vqe(payload: OptimizationVqeRequest, options?: RequestOptions): Promise<OptimizationVqeResponse> {
    return this.requestJson("/optimization/vqe", { ...options, method: "POST", body: payload });
  }

  maxcut(payload: OptimizationMaxcutRequest, options?: RequestOptions): Promise<OptimizationMaxcutResponse> {
    return this.requestJson("/optimization/maxcut", { ...options, method: "POST", body: payload });
  }

  knapsack(payload: OptimizationKnapsackRequest, options?: RequestOptions): Promise<OptimizationKnapsackResponse> {
    return this.requestJson("/optimization/knapsack", { ...options, method: "POST", body: payload });
  }

  tsp(payload: OptimizationTspRequest, options?: RequestOptions): Promise<OptimizationTspResponse> {
    return this.requestJson("/optimization/tsp", { ...options, method: "POST", body: payload });
  }

  stateTomography(payload: StateTomographyRequest, options?: RequestOptions): Promise<StateTomographyResponse> {
    return this.requestJson("/experiments/state_tomography", { ...options, method: "POST", body: payload });
  }

  randomizedBenchmarking(
    payload: RandomizedBenchmarkingRequest,
    options?: RequestOptions,
  ): Promise<RandomizedBenchmarkingResponse> {
    return this.requestJson("/experiments/randomized_benchmarking", {
      ...options,
      method: "POST",
      body: payload,
    });
  }

  quantumVolume(payload: QuantumVolumeRequest, options?: RequestOptions): Promise<QuantumVolumeResponse> {
    return this.requestJson("/experiments/quantum_volume", { ...options, method: "POST", body: payload });
  }

  t1(payload: T1ExperimentRequest, options?: RequestOptions): Promise<T1ExperimentResponse> {
    return this.requestJson("/experiments/t1", { ...options, method: "POST", body: payload });
  }

  t2Ramsey(payload: T2RamseyExperimentRequest, options?: RequestOptions): Promise<T2RamseyExperimentResponse> {
    return this.requestJson("/experiments/t2ramsey", { ...options, method: "POST", body: payload });
  }

  portfolioOptimization(
    payload: FinancePortfolioOptimizationRequest,
    options?: RequestOptions,
  ): Promise<FinancePortfolioOptimizationResponse> {
    return this.requestJson("/finance/portfolio_optimization", { ...options, method: "POST", body: payload });
  }

  portfolioDiversification(
    payload: FinancePortfolioDiversificationRequest,
    options?: RequestOptions,
  ): Promise<FinancePortfolioDiversificationResponse> {
    return this.requestJson("/finance/portfolio_diversification", { ...options, method: "POST", body: payload });
  }

  kernelClassifier(payload: KernelClassifierRequest, options?: RequestOptions): Promise<KernelClassifierResponse> {
    return this.requestJson("/ml/kernel_classifier", { ...options, method: "POST", body: payload });
  }

  vqcClassifier(payload: VqcClassifierRequest, options?: RequestOptions): Promise<VqcClassifierResponse> {
    return this.requestJson("/ml/vqc_classifier", { ...options, method: "POST", body: payload });
  }

  qsvrRegressor(payload: QsvrRegressorRequest, options?: RequestOptions): Promise<QsvrRegressorResponse> {
    return this.requestJson("/ml/qsvr_regressor", { ...options, method: "POST", body: payload });
  }

  groundStateEnergy(
    payload: NatureGroundStateEnergyRequest,
    options?: RequestOptions,
  ): Promise<NatureGroundStateEnergyResponse> {
    return this.requestJson("/nature/ground_state_energy", { ...options, method: "POST", body: payload });
  }

  fermionicMappingPreview(
    payload: NatureFermionicMappingPreviewRequest,
    options?: RequestOptions,
  ): Promise<NatureFermionicMappingPreviewResponse> {
    return this.requestJson("/nature/fermionic_mapping_preview", { ...options, method: "POST", body: payload });
  }

  private async requestJson<T>(path: string, options: RequestJsonOptions = {}): Promise<T> {
    const authMode = this.resolveAuthMode(path, options.auth);
    const headers = new Headers(options.headers ?? {});
    const requestInit: RequestInit = {
      method: options.method ?? "GET",
      headers,
      signal: options.signal,
    };

    if (options.body !== undefined) {
      headers.set("Content-Type", "application/json");
      requestInit.body = JSON.stringify(options.body);
    }

    const apiKey = options.apiKey ?? this.apiKey;
    const bearerToken = options.bearerToken ?? this.bearerToken;
    if (authMode === "apiKey") {
      if (!apiKey) {
        throw new Error(`Quantum API request to ${path} requires an API key`);
      }
      headers.set("X-API-Key", apiKey);
    } else if (authMode === "bearer") {
      if (!bearerToken) {
        throw new Error(`Quantum API request to ${path} requires a bearer token`);
      }
      headers.set("Authorization", `Bearer ${bearerToken}`);
    }

    const url = new URL(`${this.baseUrl}${path}`);
    for (const [key, value] of Object.entries(options.query ?? {})) {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    }

    const response = await this.fetchImpl(url.toString(), requestInit);
    if (!response.ok) {
      throw await buildApiError(response);
    }
    if (response.status === 204) {
      return undefined as T;
    }
    return (await response.json()) as T;
  }

  private resolveAuthMode(path: string, requested: AuthMode | undefined): Exclude<AuthMode, "auto"> {
    const mode = requested ?? this.defaultAuthMode;
    if (mode !== "auto") {
      return mode;
    }
    if (path === "/health" || path === "/portfolio.json") {
      return "none";
    }
    if (path.startsWith("/keys") || path.startsWith("/ibm/profiles")) {
      return "bearer";
    }
    return "apiKey";
  }
}

function normalizeBaseUrl(baseUrl: string): string {
  const trimmed = baseUrl.trim().replace(/\/+$/, "");
  if (!trimmed) {
    throw new Error("QuantumApiClient requires a non-empty baseUrl");
  }
  return trimmed.endsWith("/v1") ? trimmed : `${trimmed}/v1`;
}

function resolveDefaultFetchImpl(): typeof fetch {
  if (typeof window !== "undefined" && typeof window.fetch === "function") {
    return window.fetch.bind(window);
  }
  if (typeof globalThis.fetch === "function") {
    return globalThis.fetch.bind(globalThis);
  }
  throw new Error("QuantumApiClient requires fetch support. Provide options.fetchImpl in this runtime.");
}

async function buildApiError(response: Response): Promise<QuantumApiError> {
  const bodyText = await response.text();
  const headers: Record<string, string> = {};
  response.headers.forEach((value, key) => {
    headers[key] = value;
  });
  let payload: { error?: string; message?: string; details?: unknown; request_id?: string } | undefined;
  try {
    payload = JSON.parse(bodyText) as typeof payload;
  } catch {
    payload = undefined;
  }
  return new QuantumApiError({
    status: response.status,
    headers,
    bodyText,
    payload,
  });
}
