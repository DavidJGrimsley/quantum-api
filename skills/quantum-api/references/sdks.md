# Quantum API — SDK Integration Guide

**Compatibility matrix**: [`docs/sdk/compatibility-matrix.md`](../../../docs/sdk/compatibility-matrix.md)

All SDKs are in Phase 6 package-ready status. None are yet published to npm/PyPI — use the source directly or via the GitHub repo until publishing is complete.

---

## JavaScript / TypeScript SDK (`@mr.dj2u/quantum-api`)

**Status**: Package-ready (not yet published to npm)  
**Version**: 0.1.2  
**Repo path**: `sdk/js/`  
**Supported surface**: Full `/v1` REST contract  
**Auth modes**: `X-API-Key`, Supabase bearer JWT, per-request override  
**Target environments**: Node ≥ 18, browser, Expo

### Install (from GitHub, pre-publish)

```bash
# Until published to npm, install from the monorepo or a local build:
npm install /path/to/sdk/js
# or point package.json to the GitHub repo:
# "dependencies": { "@mr.dj2u/quantum-api": "github:davidjgrimsley/quantum-api#main" }
```

### Basic Usage

```typescript
import { QuantumApiClient } from '@mr.dj2u/quantum-api';

const client = new QuantumApiClient({
  baseUrl: 'https://davidjgrimsley.com/public-facing/api/quantum/v1',
  apiKey: process.env.QUANTUM_API_KEY,
});

// Health check
const health = await client.health();

// Run a Bell circuit
const result = await client.runCircuit({
  num_qubits: 2,
  operations: [
    { gate: 'h', target: 0 },
    { gate: 'cx', control: 0, target: 1 },
  ],
  shots: 1024,
});

console.log(result.counts); // { "00": 496, "11": 528 }
```

### Per-request auth override

```typescript
const result = await client.runCircuit({ ... }, {
  apiKey: 'override_key_for_this_request',
});
```

### Build from source

```bash
cd sdk/js
npm install
npm run build
```

---

## Python SDK (`quantum-api-sdk`)

**Status**: Package-ready (not yet published to PyPI)  
**Version**: 0.1.0  
**Repo path**: `sdk/python/`  
**Supported surface**: Full `/v1` REST contract  
**Auth modes**: `X-API-Key`, Supabase bearer JWT, per-request override

### Install (from GitHub, pre-publish)

```bash
# Until published to PyPI:
pip install /path/to/sdk/python
# or with uv:
uv add /path/to/sdk/python
```

### Basic Usage (sync, context-manager style)

```python
from quantum_api_sdk import QuantumApiClient

with QuantumApiClient(
    base_url="https://davidjgrimsley.com/public-facing/api/quantum/v1",
    api_key="your_api_key_here",
) as client:
    health = client.health()
    
    result = client.run_circuit(
        num_qubits=2,
        operations=[
            {"gate": "h", "target": 0},
            {"gate": "cx", "control": 0, "target": 1},
        ],
        shots=1024,
    )
    print(result["counts"])  # {"00": 496, "11": 528}
```

---

## PennyLane Plugin (`quantum-api-pennylane`)

**Status**: Package-ready (not yet published to PyPI)  
**Version**: 0.1.0  
**Repo path**: `sdk/pennylane/`  
**Device name**: `quantum.api`  
**Supported surface**: `/v1/qasm/run` (finite-shot + analytic statevector mode)  
**Auth**: `X-API-Key` via SDK client auth routing

### Install

```bash
# Requires PennyLane ≥ 0.44.1
pip install pennylane
pip install /path/to/sdk/pennylane
```

### Basic Usage

```python
import pennylane as qml

dev = qml.device(
    "quantum.api",
    wires=2,
    api_key="your_api_key_here",
    base_url="https://davidjgrimsley.com/public-facing/api/quantum/v1",
    shots=1024,
)

@qml.qnode(dev)
def bell_circuit():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.counts()

print(bell_circuit())
```

Analytic mode (no shots):

```python
dev = qml.device("quantum.api", wires=2, shots=None, ...)

@qml.qnode(dev)
def bell_statevector():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.state()
```

---

## Unreal Engine Plugin (`QuantumApi`)

**Status**: Phase 6 scaffold (integration underway)  
**Version**: 0.1.0  
**Repo path**: `sdk/unreal/`  
**Plugin file**: `sdk/unreal/QuantumApi.uplugin`  
**Supported surface**: `health`, `text/transform`, `gates/run` initially; optional `circuits/run` and `jobs/*`  
**Auth**: Backend proxy by default; optional direct `X-API-Key` in dev mode  
**Transport**: HTTP (not Unreal Python)  
**UE compatibility**: 5.4, 5.5, 5.6

### Installation

1. Copy the `sdk/unreal/` directory into your project's `Plugins/QuantumApi/` folder.
2. Regenerate project files (right-click `.uproject` → "Generate Visual Studio project files").
3. Enable the plugin in the Unreal Editor: **Edit → Plugins → Networking → Quantum API**.
4. Configure the API base URL in `Config/DefaultQuantumApi.ini`:

```ini
[/Script/QuantumApi.QuantumApiSettings]
BaseUrl=https://davidjgrimsley.com/public-facing/api/quantum/v1
ApiKey=your_key_in_dev_mode_only
```

### Basic Usage (Blueprint / C++)

```cpp
#include "QuantumApiClient.h"
#include "QuantumApiTypes.h"

// Subsystem access
UQuantumApiClient* Client = GetGameInstance()->GetSubsystem<UQuantumApiClient>();

// Health check
Client->Health(FOnQuantumHealthResponse::CreateLambda([](FQuantumHealthResponse Resp) {
    UE_LOG(LogTemp, Log, TEXT("Status: %s"), *Resp.Status);
}));

// Text transform
FQuantumTextTransformRequest Req;
Req.Text = TEXT("memory signal and quantum circuit");
Client->TextTransform(Req, FOnQuantumTextTransformResponse::CreateLambda([](auto Resp) {
    // ...
}));
```

**Note**: For production, route API calls through your own backend proxy so the API key is never shipped in the game binary. The `ApiKey` field in config is for local development only.

---

## Unity Helper (`QuantumApi.Runtime`)

**Status**: Phase 6 scaffold (not yet published to Package Manager)  
**Version**: 0.1.0  
**Repo path**: `sdk/unity/`  
**Package manifest**: `sdk/unity/package.json`  
**Supported surface**: `health`, `text/transform`, `gates/run` initially; optional `circuits/run` and `jobs/*`  
**Auth**: Backend proxy by default; optional direct `X-API-Key` in dev mode

### Installation

Install via Unity Package Manager using a local path or Git URL:

**Option A — Local path**:  
In Package Manager: **+ → Add package from disk** → select `sdk/unity/package.json`.

**Option B — Git URL** (after publishing):  
`https://github.com/davidjgrimsley/quantum-api.git?path=sdk/unity`

### Basic Usage (C#)

```csharp
using QuantumApi.Runtime;

public class QuantumExample : MonoBehaviour
{
    private QuantumApiClient _client;

    void Start()
    {
        _client = new QuantumApiClient(new QuantumApiConfig
        {
            BaseUrl = "https://davidjgrimsley.com/public-facing/api/quantum/v1",
            ApiKey = "dev_key_only",  // use backend proxy in production
        });

        StartCoroutine(RunHealthCheck());
    }

    IEnumerator RunHealthCheck()
    {
        yield return _client.Health(response =>
        {
            Debug.Log($"Quantum API status: {response.Status}");
        });
    }
}
```

---

## Godot Addon (`QuantumApiClient`)

**Status**: Phase 6 reference integration (promoted reusable addon)  
**Version**: 0.1.0  
**Repo path**: `sdk/godot/`  
**Addon path**: `sdk/godot/quantum_api_client/quantum_api_client.gd`  
**Supported surface**: `health`, `text/transform`, `gates/run` initially; expand from there  
**Auth**: Backend proxy by default; optional direct `X-API-Key` in dev mode

### Installation

1. Copy `sdk/godot/quantum_api_client/` into your project's `addons/` directory.
2. Enable in **Project → Project Settings → Plugins → Quantum API Client**.

### Basic Usage (GDScript)

```gdscript
extends Node

@onready var quantum = $QuantumApiClient

func _ready():
    quantum.base_url = "https://davidjgrimsley.com/public-facing/api/quantum/v1"
    quantum.api_key = "dev_key_only"  # use backend proxy in production
    
    var health = await quantum.health()
    print("Quantum status: ", health.status)
    
    var result = await quantum.text_transform("memory signal and quantum circuit")
    print("Transformed: ", result.transformed)
```
