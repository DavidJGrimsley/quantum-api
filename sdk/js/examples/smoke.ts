import { QuantumApiClient } from "../src/client";

async function smoke(): Promise<void> {
  const client = new QuantumApiClient({ baseUrl: "http://127.0.0.1:8000/v1" });

  const health = await client.health();
  console.log("Health", health);

  const gate = await client.runGate({ gate_type: "rotation", rotation_angle_rad: Math.PI / 2 });
  console.log("Gate", gate);
}

void smoke();
