# Quantum API Unity Helper

Package-style Unity runtime helper for the Quantum API mounted `/v1` contract.

This package is aimed at gameplay/runtime use. It includes:

- a fixed production endpoint in the client source
- a shared `QuantumApiManager` component for Inspector configuration
- direct `X-API-Key` authentication for protected routes
- coroutine and `Task` entry points built on `UnityWebRequest`
- structured `QuantumApiError` parsing for normalized API failures

## What This Is

The initial Unity pass targets the gameplay subset:

- `GET /v1/health`
- `GET /v1/echo-types`
- `POST /v1/gates/run`
- `POST /v1/random`
- `POST /v1/jobs/random`
- `GET /v1/jobs/{job_id}`
- `GET /v1/jobs/{job_id}/result`
- `POST /v1/jobs/{job_id}/cancel`
- `POST /v1/text/transform`

The package lives under `sdk/unity/` so it can later be published as a Unity package without having to reshape the repo again.

## Install

Unity Package Manager workflow:

1. Add `sdk/unity/package.json` through Unity Package Manager's local-path flow, or copy the package into `Packages/com.quantumapi.runtime`.
2. Add `QuantumApiManager` to one GameObject in your first scene.
3. Enter your API key in the Inspector. Set the timeout if needed.
4. Other scripts use `QuantumApiManager.Instance.Client`. The manager survives scene changes and removes duplicate instances.

The endpoint is fixed to `https://davidjgrimsley.com/public-facing/api/quantum/v1` in `QuantumApiClient.cs`. There is no Inspector setting or runtime option to change it; changing it requires editing the plugin source. Protected requests require an API key. This package does not offer a configurable backend-proxy URL. Do not ship a private API key in a distributed client; use a server-side integration if your game must keep credentials secret.

While in Play Mode, use the manager component's **Check Health** or **Request Random (0-1)** context-menu action to try the connection without writing code. Health also runs once at startup. Results and errors appear in Unity's Console. Leave the API key empty in scenes and enter it locally; a key saved into a scene is included in a build and can be read by others.

## Layout

- `package.json` - Unity package manifest
- `Runtime/` - runtime assembly, DTOs, client, manager, and error handling
- `Samples~/BasicUsage/` - starter MonoBehaviour example
- `CHANGELOG.md` and `LICENSE.md` - release notes and license

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
var submit = await client.SubmitRandomJobAsync(new RandomJobSubmitRequest
{
    min = 0,
    max = 3,
    provider = "ibm",
    backend_name = "ibm_fez",
    ibm_profile = "Unreal Engine Demos",
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

    await Task.Delay(5000);
}
```

For gameplay flows, keep the returned `job_id` and call `CancelJobAsync(job_id)` when the player exits before a pending hardware job reaches a terminal state.

Text transform with fallback:

```csharp
var request = new TextTransformRequest
{
    text = "memory signal and quantum circuit",
};

var response = await _client.TransformTextWithFallbackAsync(
    request,
    fallbackText: request.text
);
```

## Authentication

Default behavior:

- `health` -> public
- protected routes -> `X-API-Key`

The package has no configurable proxy URL. Keep private credentials on a server you control when building a distributed game; do not embed a private API key in a client build.

## IBM runtime jobs

Supply an existing `ibm_profile` name in a job request or use the owner's default profile. The Unity client does not administer credentials.

## Publishing Direction

This folder is intentionally shaped like a Unity package first.

- Best future fit: Unity package distribution (`sdk/unity` as the package source)
- Possible later channels: git-based UPM install, OpenUPM, Unity Asset Store, or a Fab listing that points to Unity-compatible package files

The Unreal plugin path in `sdk/unreal/` is still Unreal-specific. Unity should not be forced through the Unreal-style plugin install flow.

## Verification

For a beginner-friendly hosted smoke test:

1. Add this package to a scratch Unity project by local path.
2. Add `QuantumApiManager` to one GameObject and enter your own API key.
3. Enter Play Mode and confirm the Console logs a health response.
4. Use the manager's **Request Random (0-1)** context-menu action; confirm the result and source are logged.
5. Build a Windows standalone development player and repeat at least health plus one protected call.
