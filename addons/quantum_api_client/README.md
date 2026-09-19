# Quantum API Client for Godot

Use real quantum services from a Godot game without writing HTTP request code.
The client covers quick gameplay effects, text transformation, simulator work,
and the full IBM hardware job flow.

## Start Here

1. Copy this entire folder into your Godot project at
   `addons/quantum_api_client/`. Do not copy only `quantum_api_client.gd`.
2. In Godot, open **Project > Project Settings > Plugins** and enable
   **Quantum API Client Settings** once. It adds the Quantum API fields to
   **General > Quantum Api**, including **Default Ibm Profile**.
3. Set the base URL and choose one authentication mode below.
4. Add the runtime client to your game with the small example in
   [Sample Usage](#sample-usage).

The optional editor helper only makes settings easier to find. The actual
client is a runtime node; it has no editor dependency and the helper does not
run in an exported game.

## Choose Your Setup

| Setup | Best for | What to set |
| --- | --- | --- |
| Direct API key | Local development and a quick game-jam prototype | `backend_proxy_mode=false`, then provide `direct_api_key` |
| Backend proxy | A public build where you do not want players to extract your key | `backend_proxy_mode=true`; the addon sends no key |

For a small jam game, direct mode is the shortest path: the game sends its
configured key to Quantum API. Be aware that players can extract any key put
in a native or Web build. Rotate the key after the jam if that is acceptable
for your project. Proxy mode is the safer choice for a long-lived public game.

## Project Settings

The helper creates these values. You can also put them directly in
`project.godot`:

```ini
[quantum_api]
base_url="https://davidjgrimsley.com/public-facing/api/quantum/v1"
backend_proxy_mode=false
direct_api_key=""
default_ibm_profile=""
request_timeout_seconds=10.0
```

- `base_url`: Quantum API root. Whitespace and extra trailing slashes are safe;
  the client produces exactly one `/v1`.
- `backend_proxy_mode`: turn this **off** for a direct API-key setup; turn it
  **on** only when your own proxy adds the upstream credentials.
- `direct_api_key`: your Quantum API key for direct mode. It is intentionally
  shown as a password field in Godot.
- `default_ibm_profile`: optional name of the IBM profile to use for IBM calls.
  Leave it blank to use the API account's default IBM profile.
- `request_timeout_seconds`: how long a request may wait before returning a
  structured failure. The default is 10 seconds.

## Simulator Gates, Hardware Jobs, and Text

These are three different features:

| Feature | What happens | Does it use IBM hardware? |
| --- | --- | --- |
| `transform_text` | Quantum API transforms text and returns it immediately | No |
| `run_gate` | Runs a small gate effect and returns immediately | No; simulator only |
| `submit_circuit_job` | Queues a circuit on an IBM backend, then you poll for it | Yes |

So seeing transformed text proves the API connection works, but it does not
prove an IBM job ran. For IBM, submit a job, poll `get_circuit_job`, then fetch
`get_circuit_job_result` when the status is complete.

## AssetLib Submission Metadata

Use these values for the current AssetLib submission form:

- Asset Name: Quantum API Client
- Category: Addons > Scripts
- Asset Type: Addon
- Godot Version: 4.x (set the minimum version in the form to the oldest
  version you have validated for the release)
- License: Apache-2.0
- Repository URL: https://github.com/DavidJGrimsley/quantum-api
- Install Path Inside ZIP: addons/quantum_api_client
- Icon URL (direct, after tagging): `https://raw.githubusercontent.com/DavidJGrimsley/quantum-api/godot-v0.1.2/addons/quantum_api_client/icon.png`
- Suggested tags: `quantum`, `api`, `http`, `ibm`, `gameplay`
- AI-use disclosure: select **Yes** and disclose that AI assistance was used
  during development, with human review and automated validation of the
  shipped addon.

The icon is included in this addon folder so the Asset Library archive contains
the same branding. In the Asset Library form, use the direct `raw.githubusercontent.com`
URL above after the `godot-v0.1.2` tag exists.

## Base URL Behavior

The client normalizes either of these:

- `https://your-backend.example.com/public-facing/api/quantum`
- `https://your-backend.example.com/public-facing/api/quantum/v1`

## Failures You Can Handle

Every callback receives `(success: bool, payload: Dictionary)` exactly once.
When something fails, inspect `payload.error`, `payload.message`, and
`payload.status_code`. The client distinguishes missing direct authentication,
an unreachable server, timeout, malformed or empty JSON, request-start errors,
and HTTP errors. `transform_text` also gives you the original text as its
fallback value, so dialogue can keep moving.

## IBM Profiles (Per-User IBM Credentials)

How to set up IBM hardware:

1. Open `https://davidjgrimsley.com/public-facing/api/quantum` and sign in with an Identerest account.
2. In the `Api Keys` panel, create a Quantum API key and copy the raw key immediately (it is shown once).
3. In the `IBM Credentials` panel, create an IBM profile (`profile_name`, IBM API token, IBM instance/CRN, channel), then click verify.
4. Optionally mark one profile as default on that same public page.
5. Back in Godot, either leave **Default Ibm Profile** blank to use that API
   account default, or enter the profile name exactly as you created it.

Profile management (create/list/update/delete/verify) stays on your portfolio website.
This addon only consumes existing profile names for IBM runtime calls.

The profile is stored by Quantum API, not copied into the Godot project. Godot
only sends its profile name. For IBM-specific runtime routes, pass
`ibm_profile` explicitly or configure `default_ibm_profile` in project settings.

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
var developer_key := OS.get_environment("QUANTUM_API_KEY")
if developer_key.is_empty():
    push_error("QUANTUM_API_KEY is required for direct mode")
    return
quantum_api_client.set_api_key(developer_key)
```

IBM hardware discovery example:

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

For a real hardware run, build your circuit payload, call
`submit_circuit_job(payload, callback)`, keep the returned job ID, poll with
`get_circuit_job(job_id, callback)`, and finally call
`get_circuit_job_result(job_id, callback)`. Hardware queues are normal: do not
block the game while waiting; show progress or let the player continue.
