# Quantum API Unity Helper

Package-style Unity runtime helper for the Quantum API mounted `/v1` contract.

This scaffold is aimed at gameplay/runtime use, not editor tooling. It gives Unity projects the same baseline posture as the Godot and Unreal clients:

- mounted base URL normalization
- backend-proxy mode by default for shipped builds
- optional direct `X-API-Key` mode for local/dev/demo use
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

Current repo-local workflow:

1. Copy the `sdk/unity/` folder into a Unity project `Packages/` directory, or add it by local path in the Unity Package Manager.
2. Create a `QuantumApiClient`; the hosted production Quantum API URL is built into the package.
3. Keep `BackendProxyMode = true` for shipped builds unless you explicitly want local/dev/demo direct-key behavior.

The package default endpoint is `https://davidjgrimsley.com/api/public/quantum/v1`. Advanced local smoke tests can still override `QuantumApiClientOptions.BaseUrl`.

## Layout

- `package.json` - Unity package manifest
- `Runtime/` - runtime assembly, DTOs, client, and error handling
- `Samples~/BasicUsage/` - starter MonoBehaviour example

## Basic Usage

```csharp
using QuantumApi.Unity;
using UnityEngine;

public sealed class QuantumBootstrap : MonoBehaviour
{
    private QuantumApiClient _client;

    private void Awake()
    {
        _client = new QuantumApiClient(new QuantumApiClientOptions
        {
            BackendProxyMode = true,
            TimeoutSeconds = 15,
        });
    }

    private async void Start()
    {
        var health = await _client.HealthAsync();
        Debug.Log($"Quantum API status: {health.status}");

        var random = await _client.RandomIntAsync(0, 1);
        Debug.Log($"QRNG coin flip: {random.value} ({random.source})");
    }
}
```

Coroutine-based gate call:

```csharp
StartCoroutine(_client.RunGateCoroutine(
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
    BackendProxyMode = false,
    ApiKey = "qapi_devlocal_0123456789abcdef0123456789abcdef",
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

## Auth Modes

Default behavior:

- `health` -> public
- all other currently implemented Unity helper routes, including `random` -> no auth in backend-proxy mode
- protected routes in direct mode -> `X-API-Key`

If your own backend proxy expects bearer auth, pass a default bearer token and set `DefaultAuthMode = QuantumApiAuthMode.Bearer`, or override auth per request.

## IBM runtime jobs

Supply an existing `ibm_profile` name in a job request or use the owner's default profile. The Unity client does not administer credentials.

## Publishing Direction

This folder is intentionally shaped like a Unity package first.

- Best future fit: Unity package distribution (`sdk/unity` as the package source)
- Possible later channels: git-based UPM install, OpenUPM, Unity Asset Store, or a Fab listing that points to Unity-compatible package files

The Unreal plugin path in `sdk/unreal/` is still Unreal-specific. Unity should not be forced through the Unreal-style plugin install flow.

## Verification

For a beginner-friendly local smoke test:

1. Start the API with `uv run uvicorn quantum_api.main:app --host 127.0.0.1 --port 8000`.
2. Add this package to a scratch Unity project by local path.
3. Attach `QuantumApiExample` to an empty GameObject.
4. Keep the sample defaults for hosted testing: `BackendProxyMode = false` and the documented dev API key. For local API smoke tests only, override `QuantumApiClientOptions.BaseUrl` to `http://127.0.0.1:8000`.
5. Enter Play Mode and confirm the Console logs health, echo types, gate measurements, five QRNG coin flips, and one expected validation error.
6. Build a Windows standalone development player and repeat at least health plus one protected call.
