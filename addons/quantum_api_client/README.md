# Quantum API Godot Client

Reusable Godot runtime client for the mounted Quantum API `/v1` contract.

## What This Is

This folder is the promoted home for the reusable Godot addon/client.

- Runtime-focused, not an editor plugin
- Intended to be copied into a Godot project as `addons/quantum_api_client/`
- Supports gameplay/runtime plus IBM hardware profile usage:
  - `health_check`
  - `transform_text`
  - `run_gate`
  - `list_backends`
  - `transpile`
  - `submit_circuit_job`

## Install

1. Install this folder as `addons/quantum_api_client/` in your Godot project.
  If installing from this repository root, copy `addons/quantum_api_client/` into your game project.
2. In your game script, preload `res://addons/quantum_api_client/quantum_api_client.gd`.
3. Create the client as a child node at runtime.
4. Call `apply_project_settings()` at startup (or set values manually via setters).
5. If you plan to use direct mode, go to https://davidjgrimsley.com/public-facing/api/quantum/ to sign up and create an API key for `direct_api_key`.

## Project Settings

Add this to your `project.godot`:

```ini
[quantum_api]
base_url="https://davidjgrimsley.com/public-facing/api/quantum/v1"
backend_proxy_mode=true
direct_api_key=""
default_ibm_profile=""
```

Field usage:

- `base_url`: mounted Quantum API root (`/v1` is auto-normalized by the addon)
- `backend_proxy_mode`: when `true`, runtime endpoints can go through your backend proxy
- `direct_api_key`: API key used for protected runtime endpoints in direct mode
- `default_ibm_profile`: optional fallback profile name for IBM routes

## Layout

- `addons/quantum_api_client/quantum_api_client.gd` - shared runtime client

## AssetLib Submission Metadata

Use these values for the current AssetLib submission form:

- Asset Name: Quantum API Client
- Category: Addons > Scripts
- Godot Version: 4.x
- License: Apache-2.0
- Repository URL: https://github.com/DavidJGrimsley/quantum-api
- Install Path Inside ZIP: addons/quantum_api_client
- Icon URL (direct): https://i.imgur.com/mbMnGVA.jpeg

## Base URL Behavior

The client normalizes either of these:

- `https://your-backend.example.com/public-facing/api/quantum`
- `https://your-backend.example.com/public-facing/api/quantum/v1`

## Auth Modes

- Backend proxy mode: recommended for shipped games
- Direct API-key mode: useful for local/dev/demo setups for protected runtime routes

If required auth is missing, the addon now fails early with clear diagnostics instead of sending doomed requests.

## IBM Profiles (Per-User IBM Credentials)

How a normal hosted user gets credentials and profiles:

1. Open `https://davidjgrimsley.com/public-facing/api/quantum` and sign in with an Identerest account.
2. In the `Api Keys` panel, create a Quantum API key and copy the raw key immediately (it is shown once).
3. In the `IBM Credentials` panel, create an IBM profile (`profile_name`, IBM API token, IBM instance/CRN, channel), then click verify.
4. Optionally mark one profile as default on that same public page.

Profile management (create/list/update/delete/verify) stays on your portfolio website.
This addon only consumes existing profile names for IBM runtime calls.

For IBM-specific runtime routes, pass `ibm_profile` explicitly or configure `default_ibm_profile` in project settings.

## Sample Usage

```gdscript
const QuantumApiClientScript = preload("res://addons/quantum_api_client/quantum_api_client.gd")

var quantum_api_client: QuantumApiClient

func _ready() -> void:
    quantum_api_client = QuantumApiClientScript.new()
    add_child(quantum_api_client)
    quantum_api_client.apply_project_settings()
```

Direct API usage:

```gdscript
quantum_api_client.set_backend_proxy_mode(false)
quantum_api_client.set_api_key("your-runtime-api-key")
```

IBM hardware usage example:

```gdscript
quantum_api_client.set_backend_proxy_mode(false)
quantum_api_client.set_api_key("your-runtime-api-key")
quantum_api_client.set_default_ibm_profile("Echo Text Adventure Godot Game")

quantum_api_client.list_backends(func(success: bool, payload: Dictionary) -> void:
    print(success, payload)
, "ibm")
```
