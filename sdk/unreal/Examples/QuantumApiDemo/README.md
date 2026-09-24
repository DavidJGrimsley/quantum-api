# Quantum API UE 5.8 Demo

This is the source-controlled UE 5.8 consumer project for the Quantum API plugin. It starts a health check, then runs `rotation_angle_rad = PI / 2`, then requests one local QRNG value from `[0, 1]`.

## Quickstart

1. Install Unreal Engine 5.8 plus the Windows C++ toolchain.
2. Open `QuantumApiDemo.uproject`, allow UE to generate project files, and build `QuantumApiDemoEditor`.
3. The `.uproject` discovers the adjacent plugin for editor development. Before packaging, run `./StagePlugin.ps1` to copy it into this project's `Plugins/QuantumApi` directory.
4. In **Project Settings > Quantum API**, set the mounted `/v1` base URL and choose an auth mode:
   - **Direct API Key**: set `QUANTUM_API_KEY` in the developer machine's environment (or use the `ApiKey` fallback) for a disposable game-jam/dev key. Restart Unreal after changing it. A packaged client cannot keep this secret.
   - **Backend Proxy**: leave `ApiKey` empty and provide only the proxy's developer-owned auth header/token when needed.
5. Press Play. The default Game Mode spawns `AQuantumApiDemoActor`, whose `RunQuickstart` function is the exact callable Blueprint sequence. To customize it, make a Blueprint child of that actor and assign it to `DemoActorClass` on a Game Mode child.

Success prints health, `RY(pi/2)` measurement, and QRNG result on screen. Validation, auth, and API-down failures route to `HandleError` without blocking play.

## QRNG and IBM jobs

`GenerateRandomInt` uses `POST /v1/random`; `SubmitRandomJob` uses IBM hardware through `POST /v1/jobs/random`. Both require the developer's API-key/proxy policy. The plugin never creates API keys or stores IBM credentials; it only passes an optional `ibm_profile` name to the API. For IBM hardware testing, configure **Default IBM Profile Name** in Project Settings or set `IbmProfile` directly on the job request node.

Neither endpoint is a cryptographic or certified-randomness guarantee. Hardware jobs can incur provider usage and are intentionally not started by this demo.
