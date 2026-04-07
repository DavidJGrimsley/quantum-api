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
- `POST /v1/text/transform`

The package lives under `sdk/unity/` so it can later be published as a Unity package without having to reshape the repo again.

## Install

Current repo-local workflow:

1. Copy the `sdk/unity/` folder into a Unity project `Packages/` directory, or add it by local path in the Unity Package Manager.
2. Create a `QuantumApiClient` with your mounted base URL.
3. Keep `BackendProxyMode = true` for shipped builds unless you explicitly want local/dev/demo direct-key behavior.

Example base URLs:

- Local API: `http://127.0.0.1:8000`
- Mounted production API: `https://davidjgrimsley.com/public-facing/api/quantum`

Both normalize to `/v1` automatically.

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
            BaseUrl = "https://example.com/public-facing/api/quantum",
            BackendProxyMode = true,
            TimeoutSeconds = 15,
        });
    }

    private async void Start()
    {
        var health = await _client.HealthAsync();
        Debug.Log($"Quantum API status: {health.status}");
    }
}
```

Coroutine-based gate call:

```csharp
StartCoroutine(_client.RunGateCoroutine(
    new GateRunRequest
    {
        gate_type = "rotation",
        rotation_angle_rad = Mathf.PI / 2f,
    },
    response => Debug.Log($"Measurement: {response.measurement}"),
    error => Debug.LogWarning(error.Message)
));
```

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
- all other currently implemented Unity helper routes -> no auth in backend-proxy mode
- protected routes in direct mode -> `X-API-Key`

If your own backend proxy expects bearer auth, pass a default bearer token and set `DefaultAuthMode = QuantumApiAuthMode.Bearer`, or override auth per request.

## IBM Profiles (Per-User IBM Credentials)

How a normal hosted user gets credentials:

1. Open `https://davidjgrimsley.com/public-facing/api/quantum` and sign in with an Identerest account.
2. In the `Api Keys` panel, create a Quantum API key and copy the raw key immediately (it is shown once).
3. In the `IBM Credentials` panel, create an IBM profile (`profile_name`, IBM API token, IBM instance/CRN, channel), then click verify.
4. Optionally mark one profile as default on that same public page.

This Unity helper currently wraps gameplay endpoints only, so profile lifecycle calls are expected to run through your backend.

Backend responsibilities:

- call `/v1/ibm/profiles*` using `Authorization: Bearer <jwt_from_identerest_sign_in>`.
- return profile status/list data to the Unity UI.
- submit IBM jobs with `ibm_profile` set to the selected profile name (or omit it to use the default profile).

If you need direct profile calls in Unity before dedicated helper methods are added, issue custom `UnityWebRequest` calls to `/v1/ibm/profiles*` with `Authorization: Bearer <token>`.

## Publishing Direction

This folder is intentionally shaped like a Unity package first.

- Best future fit: Unity package distribution (`sdk/unity` as the package source)
- Possible later channels: git-based UPM install, OpenUPM, Unity Asset Store, or a Fab listing that points to Unity-compatible package files

The Unreal plugin path in `sdk/unreal/` is still Unreal-specific. Unity should not be forced through the Unreal-style plugin install flow.

## Verification

This Linux VPS repo does not include a Unity editor/runtime toolchain, so this helper should be treated as a package-ready scaffold until it has been smoke-tested inside a real Unity project.
