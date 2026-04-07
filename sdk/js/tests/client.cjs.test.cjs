const test = require("node:test");
const assert = require("node:assert/strict");

const { QuantumApiClient, QuantumApiError } = require("../dist-cjs/index.js");

test("commonjs require exports SDK symbols and performs requests", async () => {
  assert.equal(typeof QuantumApiClient, "function");
  assert.equal(typeof QuantumApiError, "function");

  const seen = [];
  const client = new QuantumApiClient({
    baseUrl: "https://example.com/public-facing/api/quantum",
    fetchImpl: async (url) => {
      seen.push(url.toString());
      return new Response(
        JSON.stringify({
          status: "healthy",
          service: "Quantum API",
          version: "0.1.0",
          qiskit_available: true,
          runtime_mode: "qiskit",
        }),
        {
          status: 200,
          headers: { "content-type": "application/json" },
        },
      );
    },
  });

  const health = await client.health();
  assert.equal(health.status, "healthy");
  assert.equal(seen[0], "https://example.com/public-facing/api/quantum/v1/health");
});