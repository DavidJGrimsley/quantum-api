# Quantum API Unity Helper

Package-style Unity runtime helper for the Quantum API mounted `/v1` contract.

This package is aimed at gameplay/runtime use. It includes:

- the hosted production endpoint for direct mode and a configurable backend proxy URL
- a shared `QuantumApiManager` component for Inspector configuration
- direct `X-API-Key` authentication or credential-free calls to your backend proxy
- coroutine and `Task` entry points built on `UnityWebRequest`
- structured `QuantumApiError` parsing for normalized API failures

## What This Is

The initial Unity pass targets the gameplay subset:

- `GET /v1/health`
- `GET /v1/echo-types`
- `POST /v1/gates/run`
- `POST /v1/topological/braid`
- `POST /v1/random`
- `POST /v1/jobs/random`
- `GET /v1/jobs/{job_id}`
- `GET /v1/jobs/{job_id}/result`
- `POST /v1/jobs/{job_id}/cancel`
- `POST /v1/text/transform`

The local Unity package lives under `sdk/unity/`. Its manifest currently declares version `1.1.0` and Unity `2021.3` as the minimum editor version.

See [QRNG Unity Demo](https://github.com/DavidJGrimsley/qrng-unity-demo) for a separate Unity project using this package.

## Install

For the `.unitypackage` from Fab, choose **Assets → Import Package → Custom Package**
in Unity, select the downloaded file, and import its contents. The scripts,
sample, and documentation appear under `Assets/QuantumApi`.

Unity Package Manager workflow for the source package:

1. In Unity Package Manager, choose **Add package from disk** and select `sdk/unity/package.json`, or copy the package into `Packages/com.quantumapi.runtime`.
2. Add `QuantumApiManager` to one GameObject in your first scene.
3. Choose direct mode and enter an API key, or enable **Backend Proxy Mode** and enter your proxy URL. Set the timeout and optional IBM defaults if needed.
4. Other scripts use `QuantumApiManager.Instance.Client`. The manager survives scene changes and removes duplicate instances. Set its connection fields before entering Play Mode; it creates the client in `Awake`.

Direct mode uses `https://davidjgrimsley.com/public-facing/api/quantum/v1` and sends the manager's API key on protected requests. Proxy mode sends requests to your proxy URL, normalized to end in `/v1`, without sending an API key or bearer token. The proxy must implement the compatible API and hold the upstream credential server-side. The Inspector shows only the connection field for the selected mode.

`RandomIntAsync` uses the local simulator or classical fallback. It is not an IBM hardware call or a cryptographic randomness source; use `SubmitRandomJobAsync` for an IBM hardware job.

While in Play Mode, use the manager component's **Check Health** or **Request Random (0-1)** context-menu action to try the connection without writing code. Health also runs once at startup. Results and errors appear in Unity's Console. Leave the API key empty in committed scenes and enter it locally; a key serialized into a scene or distributed build can be read by others.

## Layout

- `package.json` - Unity package manifest
- `Runtime/` - runtime assembly, DTOs, client, manager, and error handling
- `Samples~/BasicUsage/` - starter MonoBehaviour example
- `CHANGELOG.md` and `LICENSE.md` - release notes and license

The Fab asset package presents `Samples~/BasicUsage` as `Samples/BasicUsage`
because Unity ignores folders ending in `~` under a project's `Assets` folder.

## Basic Usage

```csharp
using QuantumApi.Unity;
using UnityEngine;

public sealed class QuantumBootstrap : MonoBehaviour
{
    private async void Start()
    {
        var client = QuantumApiManager.Instance.Client;
        var health = await client.HealthAsync();
        Debug.Log($"Quantum API status: {health.status}");

        var random = await client.RandomIntAsync(0, 1);
        Debug.Log($"QRNG coin flip: {random.value} ({random.source})");
    }
}
```

Coroutine-based gate call:

```csharp
StartCoroutine(QuantumApiManager.Instance.Client.RunGateCoroutine(
    new GateRunRequest
    {
        gate_type = "rotation",
        sendRotationAngle = true,
        rotation_angle_rad = Mathf.PI / 2f,
    },
    response => Debug.Log($"Measurement: {response.measurement}"),
    error => Debug.LogWarning(error.Message)
));
```

Typed Fibonacci braid call:

```csharp
var braid = await QuantumApiManager.Instance.Client.EvaluateBraidAsync(
    new TopologicalBraidRequest
    {
        braid_word = new[]
        {
            new BraidOperation { generator = 2, power = 1 },
        },
    });
Debug.Log($"Tau probability: {braid.fusion_probabilities.tau:P1}");
Debug.Log($"Tau amplitude: {braid.logical_state[1].real} + {braid.logical_state[1].imag}i");
```

For this single `sigma_2` crossing from the default state, the expected tau
probability is approximately `0.618034`. The included sample checks the full
two-amplitude reference vector when run in Unity.

Operations run in array order. The request defaults to three Fibonacci anyons
with total charge `tau`, initial state `0`, and no measurement. Set `measure`
and `shots` to sample; set `sendSeed=true` with `seed` for reproducible samples.
The response includes two complex amplitudes, fusion probabilities, and
optional measurement and counts. This is a simulator call, not an IBM job.
`EvaluateBraidCoroutine` provides the equivalent coroutine entry point.

Direct-key QRNG smoke test:

```csharp
var client = new QuantumApiClient(new QuantumApiClientOptions
{
    ApiKey = "YOUR_API_KEY",
});

for (var index = 0; index < 5; index += 1)
{
    var random = await client.RandomIntAsync(0, 1);
    Debug.Log($"QRNG coin flip {index + 1}: {random.value} ({random.source})");
}
```

IBM hardware QRNG job:

```csharp
var client = QuantumApiManager.Instance.Client;
var submit = await client.SubmitRandomJobAsync(new RandomJobSubmitRequest
{
    min = 0,
    max = 3,
    provider = "ibm",
    backend_name = "YOUR_IBM_HARDWARE_BACKEND",
    ibm_profile = "YOUR_EXISTING_IBM_PROFILE",
});

while (true)
{
    var status = await client.GetJobAsync(submit.job_id);
    if (status.status == "succeeded")
    {
        var result = await client.GetJobResultAsync(submit.job_id);
        Debug.Log($"IBM hardware QRNG value: {result.result.value} ({result.result.source})");
        break;
    }

    if (status.status == "failed" || status.status == "cancelled")
    {
        Debug.LogWarning(status.error != null ? status.error.message : $"Job ended: {status.status}");
        break;
    }

    await System.Threading.Tasks.Task.Delay(5000);
}
```

Replace the backend and profile placeholders with names available to your API account. An IBM hardware job may queue and incur provider usage.

For gameplay flows, keep the returned `job_id` and call `CancelJobAsync(job_id)` when the player exits before a pending hardware job reaches a terminal state.

Text transform with fallback:

```csharp
var request = new TextTransformRequest
{
    text = "memory signal and quantum circuit",
};

var response = await QuantumApiManager.Instance.Client.TransformTextWithFallbackAsync(
    request,
    fallbackText: request.text
);
```

## Authentication

Default behavior:

- `health` -> public
- protected routes -> `X-API-Key`

Direct mode requires an API key for protected routes. Proxy mode requires a valid HTTP or HTTPS URL and sends no `X-API-Key` or `Authorization` header, including when request options provide one. Keep upstream credentials on the proxy server for a distributed game.

## IBM runtime jobs

Set optional default backend and profile names on `QuantumApiManager`. Blank IBM job request fields use these defaults; explicit values take priority. The Unity client does not administer IBM credentials.

## Distribution

The Fab Unity download is a native `.unitypackage` that imports into one
`Assets/QuantumApi` folder. This source folder is also a Unity Package Manager
package for local development. It has no third-party Unity package dependencies.

The Unreal plugin in `sdk/unreal/` is a separate product format.

## Verification

For a beginner-friendly hosted smoke test:

1. Add this package to a scratch Unity project by local path.
2. Add `QuantumApiManager` to one GameObject and enter your own API key.
3. Enter Play Mode and confirm the Console logs a health response.
4. Use the manager's **Request Random (0-1)** context-menu action; confirm the result and source are logged.
5. Build a Windows standalone development player and repeat at least health plus one protected call.
