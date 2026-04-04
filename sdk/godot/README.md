# Quantum API Godot Client

Reusable Godot runtime client for the mounted Quantum API `/v1` contract.

## What This Is

This folder is the promoted home for the reusable Godot addon/client.

- Runtime-focused, not an editor plugin
- Intended to be copied into a Godot project as `addons/quantum_api_client/`
- Supports the current gameplay subset:
  - `health_check`
  - `transform_text`
  - `run_gate`

## Install

1. Copy the `addons/` folder from this directory into your Godot project root.
2. In your game script, preload `res://addons/quantum_api_client/quantum_api_client.gd`.
3. Create the client as a child node at runtime.
4. Set backend-proxy mode for production, or direct API-key mode for local/dev/demo use.

## Layout

- `addons/quantum_api_client/quantum_api_client.gd` - shared runtime client

## Base URL Behavior

The client normalizes either of these:

- `https://your-backend.example.com/public-facing/api/quantum`
- `https://your-backend.example.com/public-facing/api/quantum/v1`

## Auth Modes

- Backend proxy mode: recommended for shipped games
- Direct API-key mode: useful for local/dev/demo setups

If direct mode is enabled without an API key, the client returns a clear local error instead of sending a doomed request.

## Sample Usage

```gdscript
const QuantumApiClientScript = preload("res://addons/quantum_api_client/quantum_api_client.gd")

var quantum_api_client: QuantumApiClient

func _ready() -> void:
    quantum_api_client = QuantumApiClientScript.new()
    add_child(quantum_api_client)
    quantum_api_client.set_base_url("https://your-backend.example.com/public-facing/api/quantum")
    quantum_api_client.set_backend_proxy_mode(true)
```

Direct API usage:

```gdscript
quantum_api_client.set_backend_proxy_mode(false)
quantum_api_client.set_api_key("your-runtime-api-key")
```
