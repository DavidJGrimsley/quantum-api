import test from "node:test";
import assert from "node:assert/strict";

const { QuantumApiClient, QuantumApiError } = await import("../dist/index.js");

test("normalizes base url and appends /v1 when missing", async () => {
  const seen = [];
  const client = new QuantumApiClient({
    baseUrl: "https://example.com/public-facing/api/quantum/",
    fetchImpl: async (url) => {
      seen.push(url.toString());
      return new Response(JSON.stringify({ status: "healthy", service: "Quantum API", version: "0.1.0", qiskit_available: true, runtime_mode: "qiskit" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    },
  });

  await client.health();
  assert.equal(seen[0], "https://example.com/public-facing/api/quantum/v1/health");
});

test("uses api key by default and allows per-request bearer override", async () => {
  const authHeaders = [];
  const client = new QuantumApiClient({
    baseUrl: "https://example.com",
    apiKey: "qapi_demo_123",
    bearerToken: "jwt-token",
    fetchImpl: async (_url, init) => {
      const headers = new Headers(init?.headers);
      authHeaders.push({
        apiKey: headers.get("X-API-Key"),
        authorization: headers.get("Authorization"),
      });
      return new Response(JSON.stringify({ status: "healthy", service: "Quantum API", version: "0.1.0", qiskit_available: true, runtime_mode: "qiskit" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    },
  });

  await client.echoTypes();
  await client.listKeys();

  assert.deepEqual(authHeaders[0], { apiKey: "qapi_demo_123", authorization: null });
  assert.deepEqual(authHeaders[1], { apiKey: null, authorization: "Bearer jwt-token" });
});

test("throws structured QuantumApiError with parsed body and rate limits", async () => {
  const client = new QuantumApiClient({
    baseUrl: "https://example.com",
    apiKey: "qapi_demo_123",
    fetchImpl: async () =>
      new Response(
        JSON.stringify({
          error: "too_many_requests",
          message: "Rate limit or quota exceeded.",
          request_id: "req-123",
          details: { retry_after_seconds: 15 },
        }),
        {
          status: 429,
          headers: {
            "content-type": "application/json",
            "retry-after": "15",
            "ratelimit-limit": "600",
            "ratelimit-remaining": "0",
            "ratelimit-reset": "1712345678",
          },
        },
      ),
  });

  await assert.rejects(
    async () => client.runGate({ gate_type: "bit_flip" }),
    (error) => {
      assert.ok(error instanceof QuantumApiError);
      assert.equal(error.status, 429);
      assert.equal(error.requestId, "req-123");
      assert.equal(error.body?.error, "too_many_requests");
      assert.deepEqual(error.rateLimit, {
        limit: 600,
        remaining: 0,
        reset: 1712345678,
        retryAfter: 15,
      });
      return true;
    },
  );
});
