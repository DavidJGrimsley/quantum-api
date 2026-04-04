import { QuantumApiClient, QuantumApiError } from "../src/index.js";

async function smoke(): Promise<void> {
  const client = new QuantumApiClient({
    baseUrl: process.env.QUANTUM_API_BASE_URL ?? "http://127.0.0.1:8000",
    apiKey: process.env.QUANTUM_API_KEY ?? "dev-local-key",
  });

  try {
    const health = await client.health();
    console.log("Health", health);

    const gate = await client.runGate({
      gate_type: "rotation",
      rotation_angle_rad: Math.PI / 2,
    });
    console.log("Gate", gate);

    const transformed = await client.transformText({
      text: "memory and quantum signal",
    });
    console.log("Transform", transformed.transformed);
  } catch (error) {
    if (error instanceof QuantumApiError) {
      console.error("Quantum API error", error.status, error.code, error.requestId, error.details);
      return;
    }
    throw error;
  }
}

void smoke();
