export type GateType = "bit_flip" | "phase_flip" | "rotation";

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  qiskit_available: boolean;
  runtime_mode: "qiskit" | "classical-fallback";
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

export interface QuantumApiClientOptions {
  baseUrl: string;
  apiKey?: string;
  fetchImpl?: typeof fetch;
}

export class QuantumApiClient {
  private readonly baseUrl: string;
  private readonly apiKey?: string;
  private readonly fetchImpl: typeof fetch;

  constructor(options: QuantumApiClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, "");
    this.apiKey = options.apiKey;
    this.fetchImpl = options.fetchImpl ?? fetch;
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (init?.headers) {
      const initial = new Headers(init.headers);
      for (const [key, value] of initial.entries()) {
        headers[key] = value;
      }
    }

    if (this.apiKey) {
      headers["X-API-Key"] = this.apiKey;
    }

    const response = await this.fetchImpl(`${this.baseUrl}${path}`, {
      headers,
      ...init,
    });

    if (!response.ok) {
      const body = await response.text();
      throw new Error(`Quantum API request failed (${response.status}): ${body}`);
    }

    return (await response.json()) as T;
  }

  health(): Promise<HealthResponse> {
    return this.request<HealthResponse>("/health");
  }

  echoTypes(): Promise<EchoTypesResponse> {
    return this.request<EchoTypesResponse>("/echo-types");
  }

  runGate(payload: GateRunRequest): Promise<GateRunResponse> {
    return this.request<GateRunResponse>("/gates/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  transformText(payload: TextTransformRequest): Promise<TextTransformResponse> {
    return this.request<TextTransformResponse>("/text/transform", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }
}
