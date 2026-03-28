# Quantum API JS SDK (Scaffold)

Typed TypeScript client scaffold for Quantum API `/v1` endpoints.

## Usage

```ts
import { QuantumApiClient } from "@quantum-api/sdk";

const client = new QuantumApiClient({
  baseUrl: process.env.EXPO_PUBLIC_QUANTUM_API_BASE_URL ?? "http://127.0.0.1:8000/v1",
});

const gate = await client.runGate({
  gate_type: "rotation",
  rotation_angle_rad: Math.PI / 2,
});

console.log(gate.measurement, gate.superposition_strength);
```
