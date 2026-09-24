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
3. Choose direct mode and enter an API key, or enable **Backend Proxy Mode** and enter your proxy URL. Set the timeout and optional IBM defaults if needed.
4. Other scripts use `QuantumApiManager.Instance.Client`. The manager survives scene changes and removes duplicate instances.

Direct mode uses `https://davidjgrimsley.com/public-facing/api/quantum/v1` and sends the manager's API key on protected requests. Proxy mode sends requests to your proxy URL, normalized to end in `/v1`, without sending an API key or bearer token. The proxy must implement the compatible API and hold the upstream credential server-side. The Inspector shows only the connection field for the selected mode.

While in Play Mode, use the manager component's **Check Health** or **Request Random (0-1)** context-menu action to try the connection without writing code. Health also runs once at startup. Results and errors appear in Unity's Console. Leave the API key empty in committed scenes and enter it locally; a key serialized into a scene or distributed build can be read by others.

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

Direct mode requires an API key for protected routes. Proxy mode requires a valid HTTP or HTTPS URL and sends no `X-API-Key` or `Authorization` header, including when request options provide one. Keep upstream credentials on the proxy server for a distributed game.

## IBM runtime jobs

Set optional default backend and profile names on `QuantumApiManager`. Blank IBM job request fields use these defaults; explicit values take priority. The Unity client does not administer IBM credentials.

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
