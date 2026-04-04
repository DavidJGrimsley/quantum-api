export interface QuantumApiErrorPayload {
  error?: string;
  message?: string;
  details?: unknown;
  request_id?: string;
}

export interface QuantumApiRateLimit {
  limit?: number;
  remaining?: number;
  reset?: number;
  retryAfter?: number;
}

export class QuantumApiError extends Error {
  readonly status: number;
  readonly code?: string;
  readonly details?: unknown;
  readonly requestId?: string;
  readonly headers: Record<string, string>;
  readonly bodyText: string;
  readonly body?: QuantumApiErrorPayload;
  readonly rateLimit: QuantumApiRateLimit;

  constructor(input: {
    status: number;
    bodyText: string;
    payload?: QuantumApiErrorPayload;
    headers: Record<string, string>;
  }) {
    const message = input.payload?.message ?? `Quantum API request failed with status ${input.status}`;
    super(message);
    this.name = "QuantumApiError";
    this.status = input.status;
    this.code = input.payload?.error;
    this.details = input.payload?.details;
    this.requestId = input.payload?.request_id;
    this.headers = input.headers;
    this.bodyText = input.bodyText;
    this.body = input.payload;
    this.rateLimit = {
      limit: parseOptionalNumber(input.headers["ratelimit-limit"]),
      remaining: parseOptionalNumber(input.headers["ratelimit-remaining"]),
      reset: parseOptionalNumber(input.headers["ratelimit-reset"]),
      retryAfter: parseOptionalNumber(input.headers["retry-after"]),
    };
  }
}

function parseOptionalNumber(value: string | undefined): number | undefined {
  if (value === undefined) {
    return undefined;
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}
