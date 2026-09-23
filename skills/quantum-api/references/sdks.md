# First-party client guide

Check the client's current source and README before using a method: the REST
API can gain endpoints before every SDK wrapper does. Supply an existing API
key or a backend proxy. Administrative key and IBM credential operations are
outside an integration agent's scope.

## JavaScript and TypeScript

`@mr.dj2u/quantum-api` 0.1.2 is published on npm. It supports browser, Node,
and Expo use. For a distributed app, call a backend proxy so the key stays on
the server. The current typed client has no wrapper for `/v1/random` or
`/v1/jobs/random`; use authenticated HTTP for those routes. When the proxy
adds upstream authentication, pass `{ auth: "none" }` to protected SDK calls.

```bash
npm install @mr.dj2u/quantum-api
```

```ts
import { QuantumApiClient } from "@mr.dj2u/quantum-api";

const client = new QuantumApiClient({
  baseUrl: "https://davidjgrimsley.com/public-facing/api/quantum/v1",
  apiKey: process.env.QUANTUM_API_KEY,
});
const health = await client.health();
const circuit = await client.runCircuit({
  num_qubits: 2,
  operations: [{ gate: "h", target: 0 }, { gate: "cx", control: 0, target: 1 }],
  shots: 1024,
});
```

See [the JS SDK README](../../../sdk/js/README.md) for current methods and
authentication options.

## Python and PennyLane

`quantum-api-sdk` 0.1.0 and `quantum-api-pennylane` 0.1.0 are published on
PyPI. The Python client is synchronous. Its current method list likewise
lacks dedicated random wrappers; use authenticated HTTP for the QRNG routes.

```bash
pip install quantum-api-sdk quantum-api-pennylane
```

```python
from quantum_api_sdk import QuantumApiClient

with QuantumApiClient(
    base_url="https://davidjgrimsley.com/public-facing/api/quantum/v1",
    api_key="supplied-runtime-key",
) as client:
    health = client.health()
    result = client.run_circuit({
        "num_qubits": 2,
        "operations": [{"gate": "h", "target": 0}, {"gate": "cx", "control": 0, "target": 1}],
        "shots": 1024,
    })
```

PennyLane device name: `quantum.api`. It executes through `/v1/qasm/run` and
supports finite-shot counts or analytic statevector mode. Consult
[the plugin README](../../../sdk/pennylane/README.md) for QNode examples.

## Unreal Engine

The `sdk/unreal/` plugin is version `0.3.0-beta` for Unreal Engine 5.8 Win64.
It is a runtime HTTP client for Blueprint and C++; UEFN is unsupported.
Copy the plugin to `<Project>/Plugins/QuantumApi`, enable it, and configure
**Project Settings → Quantum API**. Direct mode uses the fixed hosted API URL;
proxy mode uses the configured backend proxy URL. The plugin supports local
random integers, circuit and QASM calls, IBM jobs, and allowlisted advanced
routes. It retries safe reads only, never submissions or random requests.
Use [Setup and Use](../../../sdk/unreal/Docs/SetupAndUse.md) for exact nodes,
settings, and packaging steps.

## Unity

The merged `sdk/unity/` package is version `0.1.0`. Install the folder using
Unity Package Manager's local path option. Its `QuantumApi.Unity` client has
`RandomIntAsync(min, max)` and coroutine support, plus
`SubmitRandomJobAsync`, `GetJobAsync`, `GetJobResultAsync`, and
`CancelJobAsync`. In version 0.1.0, construct `QuantumApiClient` with
`QuantumApiClientOptions`; see [the Unity README](../../../sdk/unity/README.md)
for the exact configuration and sample.

[PR #19](https://github.com/DavidJGrimsley/quantum-api/pull/19) proposes a
shared `QuantumApiManager` and package version 0.2.0. That interface is
pending and must not be used as the default guidance until it merges.

## Godot

The reusable addon is at `addons/quantum_api_client/` and its current release
is 0.1.2. Copy the entire folder into the game's `addons/` directory.
Enable **Quantum API Client Settings** once in Project Settings to register
its configuration fields, then instantiate the runtime client node. Direct
mode uses a supplied key; proxy mode sends no API key. The client handles
health, gates, text, backend discovery, transpilation, and IBM circuit jobs.
See [the addon README](../../../addons/quantum_api_client/README.md) for its
method signatures, timeout behavior, and one-callback error handling.
