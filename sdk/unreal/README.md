# Quantum API Unreal Plugin

`QuantumApi` is a UE 5.8 Runtime plugin for Windows 64-bit (Win64) projects that call the Quantum API `/v1` contract. The plugin does not support UEFN.
It gives Blueprint and C++ developers async nodes/calls for gates, circuits,
QASM, QRNG, IBM jobs, and the allowlisted advanced API operations.

The plugin requires internet access and Quantum API access for protected
operations. Obtain an existing API key from the owner and keep it in a secure
development secret store. Direct API-key mode is for development only;
shipped games should call a backend proxy that keeps the key server-side.
See [Docs/SetupAndUse.md](Docs/SetupAndUse.md) for supported setup, first use,
and troubleshooting. Public documentation: https://davidjgrimsley.com/public-facing/api/quantum/ue-plugin.

## Start here: what the Blueprint pins mean

You do not need to be a quantum-computing expert to begin.

- A white execution pin controls when an async request starts.
- A `Request` pin is the little form you fill out before sending the request.
- `Options` is optional. Leave it empty for normal use.
- `On Success` receives the API response.
- `On Error` receives a safe error object without freezing gameplay.

Unreal turns C++ names into slightly awkward labels. For example,
`Quantum Api Circuit Definition` means “the data form that describes one
quantum circuit.” It is not an asset or special Unreal system.

A `struct` is a bundle of related fields. A `Circuit Operation` is one gate
step, such as “apply an H gate to qubit 0.” An `array` is a list. Therefore an
“array of circuit operation structures” means “the ordered list of gate steps
in the circuit.”

For a first test, use these nodes in order:

1. `Health Check`
2. `Run Gate`
3. `Generate Random Int`
4. `Run Circuit`
5. `List Backends`
6. `Submit Random Job`

## Install

1. Copy the `QuantumApi` plugin folder into `<YourProject>/Plugins/QuantumApi`.
2. Open the project, enable **Quantum API** in the Plugin Browser if Unreal asks,
   and build only if Unreal says the plugin needs compiling.
3. Open **Project Settings → Quantum API** and choose an authentication mode.

The source-controlled UE 5.8 build harness is
[Examples/QuantumApiDemo](Examples/QuantumApiDemo/README.md). It is a demo,
not something a game team must ship or install with the plugin.

## API access prerequisite

Protected requests require internet access and an active Quantum API key, or a
backend proxy that authenticates requests on the game's behalf. Enter a key
supplied by the owner in **Project Settings → Quantum API → API Key** for local
development. Do not put a production key in a distributed game. For a shipped
game, select **Backend Proxy** and route requests through a service you control;
that service should keep the Quantum API key private and apply your own access
controls. API access is required; the plugin does not issue keys.

**Supported target:** Unreal Engine 5.8, Win64. UEFN is unsupported because the
plugin makes runtime API requests.

## Project Settings: choose one mode

### Direct API Key — development, demos, and game jams

Select **Direct API Key** and enter a Quantum API key. The field is visually
masked, but Unreal project configuration is not a secure secret store. The
plugin always calls this hosted API URL in Direct mode:

`https://davidjgrimsley.com/public-facing/api/quantum/v1`

There is deliberately no editable Base URL. A localhost or stale `BaseUrl=`
entry cannot redirect Direct-mode requests.

Do not ship a direct API key in a packaged game: a player can extract it.

### Backend Proxy — packaged production games

Select **Backend Proxy** and enter your own **Backend Proxy URL**. The plugin
sends no Quantum API key in this mode. Your server should expose the compatible
Quantum API `/v1` contract, keep its upstream Quantum API key in its server
secret manager, and enforce whatever player/session authorization it needs.

The URL can end with `/v1` or omit it; the plugin normalizes it to the mounted
`/v1` contract. Leaving the Proxy URL blank returns a local configuration error
before any request is sent.

`Request Timeout Seconds` limits one HTTP attempt. The Reliability section
retries safe GET reads only; POSTs and cancellations are never retried, which
prevents duplicate jobs, charges, or changed random values.

## IBM hardware

The plugin never stores IBM tokens or creates IBM profiles. Those credentials
remain on the Quantum API service. Unreal stores only non-secret names:

- **Default IBM Profile Name**: which service-side IBM profile to use when a
  request leaves `IbmProfile` blank.
- **Default IBM Hardware Backend**: which IBM machine to target when a job or
  Transpile request leaves `Backend Name` blank.

Use `List Backends` with `Provider = ibm` to discover available names. A
backend typed directly into a node always wins over the Project Settings
default. Circuit/QASM/QRNG jobs and IBM-targeted Transpile calls fail locally
with a useful error if neither supplies a backend.

IBM hardware access, queues, and usage limits still apply. The API label
`ibm-hardware` does **not** mean cryptographic or certified randomness.

## Blueprint quickstart

`Health Check` confirms the service is reachable and has no request body.

For `Run Gate`, use:

- `Gate Type`: `rotation`
- `Send Rotation Angle`: checked
- `Rotation Angle Rad`: `1.57079632679` (`PI / 2`)

The response has a `Measurement`, usually `0` or `1`.

`Generate Random Int` calls QRNG with inclusive integer bounds. For a
coin-flip-style test, use `Min = 0` and `Max = 1`. The response identifies its
source as `qiskit-simulator` or `classical-fallback`; neither is a claim of
cryptographic randomness.

### Run Circuit in plain English

`Run Circuit` means: “make this many qubits, run these gate steps in order,
then sample the answer this many times.” Its important fields are:

- `Request Circuit Num Qubits`: number of qubit wires. Start with `1`.
- `Request Circuit Operations`: the ordered list of gate steps.
- `Request Shots`: how many samples to take. Start with `1024`.
- `Request Include Statevector`: advanced simulator output; leave unchecked
  while learning.
- `Request Send Seed` and `Request Seed`: deterministic simulator controls;
  leave unchecked while learning.

To make `Request Circuit Operations`, create an array of `Quantum Api Circuit
Operation` values. Promote the pin to a variable if you want to edit its
default list in the Details panel.

Tiny first circuit:

- `Num Qubits`: `1`
- `Operations`: one operation with `Gate = h`, `Target = 0`
- `Shots`: `1024`

That puts one qubit into a superposition and samples it.

### Request Options

Most projects leave `Options` empty. It is only for advanced per-call cases:

- `Override Api Key`: a different direct-development key for this call.
- `Extra Headers`: custom headers for your own backend proxy. The plugin never
  logs their values and never invents a bearer-auth header.

## C++ integration

Blueprint is not the only way to use the plugin. The demo’s
[`QuantumApiDemoActor.cpp`](Examples/QuantumApiDemo/Source/QuantumApiDemo/QuantumApiDemoActor.cpp)
is a C++ Actor that uses the same async-action classes exposed as Blueprint
nodes.

Add `QuantumApi` to your game module’s dependencies, then include
`QuantumApiAsyncActions.h` and `QuantumApiTypes.h`:

```csharp
PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "QuantumApi" });
```

From an Actor or UObject, retain the action as a `UPROPERTY(Transient)` member,
bind its success/error delegates, and activate it:

```cpp
void AMyActor::CheckQuantumApi()
{
    const FQuantumApiRequestOptions Options;
    ActiveHealthAction = UQuantumApiHealthAsyncAction::HealthCheck(this, Options);
    ActiveHealthAction->OnSuccess.AddDynamic(this, &AMyActor::HandleHealth);
    ActiveHealthAction->OnError.AddDynamic(this, &AMyActor::HandleQuantumError);
    ActiveHealthAction->Activate();
}
```

```cpp
UPROPERTY(Transient)
TObjectPtr<UQuantumApiHealthAsyncAction> ActiveHealthAction;

UFUNCTION()
void HandleHealth(FQuantumApiHealthResponse Response);

UFUNCTION()
void HandleQuantumError(FQuantumApiError Error);
```

For an advanced fully native integration, `FQuantumApiClient` is also public.
Keep its instance alive until its callback runs; it is asynchronous and should
be stored as a long-lived member, not created as a temporary stack object.

## Available operations

Typed success payloads are available for `Health Check`, `Run Gate`,
`Transform Text`, and `Generate Random Int`.

Named JSON-result async actions cover `Get Echo Types`, `Run Circuit`, `List
Backends`, `Transpile`, QASM import/export/run, and circuit/QASM/QRNG job
submission, status, result, and cancellation.

`Call Advanced Json` exposes a fixed allowlist of 22 API catalog, algorithm,
optimization, experiment, finance, ML, and nature operations. In particular,
the catalog option is the API metadata endpoint `/portfolio.json`, not finance
portfolio optimization. Credential lifecycle routes, IBM profile management,
metrics, and arbitrary paths are intentionally unavailable.

The checked-in [endpoint coverage manifest](contract/endpoint-coverage.json)
covers all 39 non-credential `/v1` operations.

## Distribution and validation

Distribute the `QuantumApi` plugin directory—descriptor, `Config`, `Source`,
`Resources`, and UE-version-matched binaries where applicable. Do not include
the demo project or credentials.

Validate a release in a fresh blank Blueprint project: install the plugin,
enable it, configure Direct mode for a disposable test key or Proxy mode for a
real proxy, then build/package and confirm the async nodes work.

Run repository contract validation from the repository root:

```powershell
uv run pytest tests/test_unreal_plugin_contract.py -q
```

On a UE 5.8 host, run `QuantumApi.Runtime.Transport` from Unreal Automation,
test the `RY(PI/2)` and QRNG flows in PIE, then package and smoke-test the
consumer project.

## Common errors

- **Unauthorized (401):** configure an existing key in Direct mode, or confirm that your proxy adds `X-API-Key`.
- **Forbidden (403):** confirm the account/key has access to that operation and
  that any IBM service-side profile and backend are configured.
- **Connection or timeout errors:** check internet access, the API service
  status, proxy URL, and timeout setting. Direct mode uses the hosted API URL;
  it cannot be changed in plugin settings.
- **Nodes are missing:** confirm the plugin is enabled, the project is Win64,
  and Unreal has compiled the plugin for UE 5.8.
