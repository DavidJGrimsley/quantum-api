# Quantum API Unreal Plugin

`QuantumApi` is a UE 5.8 Runtime plugin for the mounted Quantum API `/v1` contract. It provides Blueprint async actions, never blocks the game thread, and ships as a project plugin.

## Read this first if Unreal/quantum pins look confusing

The Blueprint nodes are async HTTP calls wrapped in Unreal-friendly pins. You do
not need to be a quantum computing expert to start.

Think of each node like this:

- The white execution pins say when the request starts.
- The `Request` pins are a form you fill out before sending the request.
- The `Options` pin is optional auth/proxy override data. Leave it empty for normal use.
- `On Success` gives you the API response.
- `On Error` gives you a safe error object instead of freezing gameplay.

Unreal turns C++ names into awkward Blueprint labels. For example,
`Quantum Api Circuit Definition` means "the small data form that describes a
quantum circuit." It is not a separate asset, class, or advanced Unreal system.

A `struct` means "a bundle of related fields." A `Circuit Operation` struct is
one step in a circuit, such as "apply an H gate to qubit 0." An `array` means a
list. So "array of circuit operation structures" just means "the ordered list of
gate steps in the circuit."

If you are brand new, start with these nodes in this order:

1. `Health Check`
2. `Run Gate`
3. `Generate Random Int`
4. `Run Circuit`
5. `List Backends`
6. `Submit Random Job`

Do not start with `Run Circuit` unless you specifically want to build a multi-step
quantum circuit. `Run Gate` and `Generate Random Int` are much easier first tests.

## Install

1. Copy `sdk/unreal` to `<YourProject>/Plugins/QuantumApi`.
2. Regenerate project files, build, then enable **Quantum API** in Unreal's Plugin Browser if needed.
3. Put configuration in the host project's `Config/DefaultGame.ini` (rather than relying on a plugin-shipped secret):

```ini
[/Script/QuantumApi.QuantumApiSettings]
BaseUrl="https://davidjgrimsley.com/public-facing/api/quantum/v1"
AuthMode=BackendProxy
ApiKey=
bUseEnvironmentApiKey=True
ApiKeyEnvironmentVariable=QUANTUM_API_KEY
BearerToken=
DefaultIbmProfile=
RequestTimeoutSeconds=10.000000
MaxReadRetries=2
MaxRetryDelaySeconds=5.000000
```

The source-controlled UE 5.8 build harness is [Examples/QuantumApiDemo](Examples/QuantumApiDemo/README.md).

## Authentication and production posture

- **Direct API Key** sends `X-API-Key` from Plugin Settings or per-call request options. For local development it first reads `QUANTUM_API_KEY` from the developer machine, then falls back to the Plugin Settings value. Restart Unreal after changing an environment variable. It is for local development, demos, and game jams only: a key packaged into a client can be extracted.
- **Backend Proxy** never sends the configured API key. Supply your own bearer/custom headers when your proxy needs them, and keep the upstream key server-side.
- The plugin intentionally does **not** create/revoke API keys or store/edit IBM credentials. For IBM routes, it accepts only an `ibm_profile` name; the service resolves that profile for the key owner. You can set a non-secret `DefaultIbmProfile` in Project Settings, then override it per Blueprint request when needed.
- Credential values are never logged by the plugin.

## Demo and distribution

`Examples/QuantumApiDemo` is a disposable verification harness, not a required dependency for a game using the plugin. Its demo actor runs `Health Check -> RY(pi/2) -> Generate Random Int(0, 1)` and shows either each result or one safe error. A developer using the plugin later installs `QuantumApi` in their own project's `Plugins/` directory, enables it, and uses the Blueprint async nodes directly.

For a release, distribute the `QuantumApi` plugin directory (descriptor, `Config`, `Source`, `Resources`, and UE-version-matched binaries when applicable), not the demo or any credentials. Validate the release in a newly created blank consumer project: enable the plugin, configure a non-secret proxy URL, build Development Editor and Shipping, package Win64, and confirm the packaged game reaches the proxy without exposing an upstream API key.

## Blueprint surface

### The three easiest nodes

`Health Check` confirms the service is reachable. It does not need a request
body.

`Run Gate` runs one simple gate. For the demo flow:

- `GateType`: `rotation`
- `bSendRotationAngle`: checked
- `RotationAngleRad`: `1.57079632679`

That angle is pi/2. The response includes `Measurement`, usually `0` or `1`.

`Generate Random Int` asks the QRNG endpoint for a bounded integer:

- `Min`: lowest allowed value
- `Max`: highest allowed value

For a coin-flip style test, use `Min = 0` and `Max = 1`.

### What the Run Circuit pins mean

`Run Circuit` is for a circuit with one or more operations. In plain English,
you are saying: "create N qubits, run this ordered list of gates, then measure
the result this many times."

The pins from the split request struct mean:

- `Request Circuit Num Qubits`: how many qubits/wires the circuit has. Start with `1`.
- `Request Circuit Operations`: the list of gate steps to run, in order.
- `Request Shots`: how many times to sample the circuit. Start with `1024`.
- `Request Include Statevector`: advanced simulator output. Leave unchecked at first.
- `Request Send Seed`: whether to send a deterministic simulator seed. Leave unchecked at first.
- `Request Seed`: the seed value. It only matters if `Request Send Seed` is checked.
- `Options`: optional per-call auth/proxy overrides. Leave it empty for normal project settings.

To build `Request Circuit Operations` in Blueprint, make an array of
`Quantum Api Circuit Operation` values. Each value is one gate instruction:

- `Gate`: gate name such as `h`, `x`, `rx`, `ry`, `rz`, or `cx`.
- `Target`: the qubit index the gate acts on. The first qubit is `0`.
- `bSendTheta` and `Theta`: only needed for rotation gates like `rx`, `ry`, `rz`.
- `bSendControl` and `Control`: only needed for controlled gates like `cx`.

Tiny first circuit example:

- `Num Qubits`: `1`
- `Operations`: one operation with `Gate = h`, `Target = 0`
- `Shots`: `1024`
- `Include Statevector`: unchecked
- `Send Seed`: unchecked

That creates one qubit, puts it into a superposition with an H gate, and samples
the result.

### What Request Options means

Most projects can leave `Options` alone. It exists for advanced cases:

- `Override Api Key`: use a different API key for this one call.
- `Override Bearer Token`: send a different user/proxy token for this one call.
- `Extra Headers`: send custom headers to your own backend proxy.

For game-jam/direct-key testing, configure Project Settings -> Quantum API and
leave `Options` empty on the nodes.

Typed success payloads are available for:

- `Health Check`, `Run Gate`, `Transform Text`, and `Generate Random Int`.
- `Generate Random Int` calls `POST /v1/random` with inclusive signed 32-bit bounds. Its result identifies `qiskit-simulator` or `classical-fallback`—neither is a cryptographic-randomness guarantee.

Named JSON-result async actions accept typed request structs for the remaining runtime core:

- `Get Echo Types`, `Run Circuit`, `List Backends`, `Transpile`.
- `Import QASM`, `Export QASM`, `Run QASM`.
- `Submit Circuit Job`, `Submit QASM Job`, `Submit Random Job`, `Get Job Status`, `Get Job Result`, `Cancel Job`.

`Call Advanced Json` exposes a fixed allowlist of 22 portfolio/algorithms/optimization/experiments/finance/ML/nature operations. It takes a JSON request body and returns raw JSON alongside status, request ID, and response headers. It cannot call `/v1/keys*`, `/v1/ibm/profiles*`, metrics, or arbitrary paths.

The checked-in [endpoint coverage manifest](contract/endpoint-coverage.json) covers all 39 non-credential `/v1` operations: 17 named core actions plus 22 advanced JSON actions.

## 30-minute QRNG and gate quickstart

1. Set a mounted `/v1` base URL and choose **Direct API Key** for a disposable game-jam key, or **Backend Proxy** for a production-safe path.
2. From a Blueprint event, call **Run Gate** with `gate_type = rotation`, `bSendRotationAngle = true`, and `rotation_angle_rad = 1.57079632679` (`PI / 2`).
3. On Success, read `measurement`; on Error, route `FQuantumApiError` to gameplay-safe UI/logging.
4. Call **Generate Random Int** with `Min = 0`, `Max = 1`; read `value` and `source` on Success.

All requests are async. GET health/backend/job reads retry at most twice for transport, 429, 502, 503, or 504 failures; POSTs and cancellation are never retried, preventing duplicate jobs, charges, and changed random results.

## QRNG hardware jobs

`Submit Random Job` calls `POST /v1/jobs/random` and uses the same status/result/cancel actions as circuit/QASM jobs. To opt into IBM hardware from Blueprint, set **Default IBM Profile Name** in Project Settings or fill the request struct's `IbmProfile`, choose an IBM `BackendName` such as the backend returned by `List Backends` with `Provider = ibm`, then submit the job and poll `Get Job Status` / `Get Job Result`. The profile name is not a secret; the IBM token and instance live on the Quantum API service.

IBM hardware availability, account access, queue time, and usage limits apply. Hardware output is labelled by the API as `ibm-hardware`; it is not a cryptographic or certified-randomness claim.

## Validation

Run backend/static contract validation from the repository root:

```powershell
uv run pytest tests/test_unreal_plugin_contract.py -q
```

On a UE 5.8 host, generate project files for the demo, build the Editor and Shipping targets, run `QuantumApi.Runtime.Transport` from Unreal Automation, test the `RY(π/2)` and QRNG flows in PIE, then package and smoke-test after staging the plugin under the demo project's `Plugins/` directory. The automation spec uses an injected mock transport to cover serialization, auth headers, response metadata/errors, request IDs, QRNG bounds, 429 retry policy, and no duplicate POST random request.
