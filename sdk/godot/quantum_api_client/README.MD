# Quantum API Godot Client

Reusable Godot runtime client for the mounted Quantum API `/v1` contract.

## What This Is

This folder contains the reusable runtime script. The distributable addon, including the optional Project Settings editor helper, is in [`addons/quantum_api_client/`](../../../addons/quantum_api_client/README.md).

For a community Godot project, see the [Quantum Jam Godot project](https://github.com/ReneJSchwartz/quantum-jam-2025-choose-your-own-adventure/tree/main/godot_project).

- Runtime script with no editor dependency
- Installed through the repository's `addons/quantum_api_client/` folder
- Supports gameplay/runtime plus IBM hardware profile usage:
  - `health_check`
  - `transform_text`
  - `run_gate`
  - `list_backends`
  - `transpile`
  - `submit_circuit_job`

## Install

1. Copy the repository's `addons/quantum_api_client/` folder into your Godot project at the same path. It includes the runtime script and optional editor settings helper.
2. In your game script, preload `res://addons/quantum_api_client/quantum_api_client.gd`.
3. Create the client as a child node at runtime.
4. Call `apply_project_settings()` at startup (or set values manually via setters).
5. Shipped games should use backend-proxy mode. Direct mode is only for a
   developer-controlled local smoke test; read its short-lived key from a
   process environment variable at runtime rather than putting it in project
   settings or build inputs.

## Project Settings

Add this to your `project.godot`:

```ini
[quantum_api]
base_url="https://davidjgrimsley.com/public-facing/api/quantum/v1"
backend_proxy_mode=true
direct_api_key=""
default_ibm_profile=""
request_timeout_seconds=10.0
```

Field usage:

- `base_url`: mounted Quantum API root (`/v1` is auto-normalized by the addon)
- `backend_proxy_mode`: when `true`, runtime endpoints can go through your backend proxy
- `direct_api_key`: optional API key used only by a developer-controlled direct
  mode runtime; leave it empty in committed settings and all distributed builds
- `default_ibm_profile`: optional fallback profile name for IBM routes
- `request_timeout_seconds`: positive REST timeout in seconds (defaults to `10.0`)

## Layout

- `addons/quantum_api_client/quantum_api_client.gd` - shared runtime client

The runtime script does not need the editor helper to run. You can enable **Quantum API Client Settings** in **Project Settings > Plugins** to edit its settings in the Inspector, or set them directly in `project.godot`.

## AssetLib Submission Metadata

Use the [distributable addon's current metadata](../../../addons/quantum_api_client/README.md#assetlib-submission-metadata) when preparing an AssetLib release.

## Base URL Behavior

The client normalizes either of these:

- `https://your-backend.example.com/public-facing/api/quantum`
- `https://your-backend.example.com/public-facing/api/quantum/v1`

## Auth Modes

- Backend proxy mode: recommended for shipped games. The addon sends no
  `X-API-Key`; your narrowly scoped server-side gateway authenticates upstream.
- Direct API-key mode: useful only for local/dev/demo setups for protected
  runtime routes.

If required auth is missing, the addon now fails early with clear diagnostics instead of sending doomed requests.

Never embed a live API key in `project.godot`, source control, a native build,
or a Web export. Anything shipped to a player can be extracted. Use a
credential-free proxy endpoint for public builds, and inject a fresh key through
the local process environment only for a developer-only direct-mode smoke test.

## IBM Profiles

Use an existing profile name supplied by the API owner, or leave `default_ibm_profile` blank to use the owner's default. The addon sends only the name for IBM runtime calls; it does not manage credentials. You can override the configured name with `ibm_profile` on a call.

## Sample Usage

```gdscript
const QuantumApiClientScript = preload("res://addons/quantum_api_client/quantum_api_client.gd")

var quantum_api_client: QuantumApiClient

func _ready() -> void:
    quantum_api_client = QuantumApiClientScript.new()
    add_child(quantum_api_client)
    quantum_api_client.apply_project_settings()
```

Developer-only direct API usage (never ship this path):

```gdscript
quantum_api_client.set_backend_proxy_mode(false)
var developer_key := OS.get_environment("QUANTUM_API_KEY")
if developer_key.is_empty():
    push_error("QUANTUM_API_KEY is required for this local direct-mode test")
    return
quantum_api_client.set_api_key(developer_key)
```

IBM hardware usage example:

```gdscript
quantum_api_client.set_backend_proxy_mode(false)
var developer_key := OS.get_environment("QUANTUM_API_KEY")
if developer_key.is_empty():
    push_error("QUANTUM_API_KEY is required for this local direct-mode test")
    return
quantum_api_client.set_api_key(developer_key)
quantum_api_client.set_default_ibm_profile("Echo Text Adventure Godot Game")

quantum_api_client.list_backends(func(success: bool, payload: Dictionary) -> void:
    print(success, payload)
, "ibm")
```
