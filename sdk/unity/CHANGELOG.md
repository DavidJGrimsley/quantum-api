# Quantum API Unity package changelog

## 1.0.0

- Fixed the built-in hosted endpoint to use the canonical `/public-facing/api/quantum/v1` route.
- Removed the nonfunctional backend-proxy toggle; protected requests now use the configured API key, and the package has no editable URL or proxy endpoint.
- Restored `QuantumApiManager` after scene load when Unity disables both domain and scene reload.
- Promoted the breaking URL/auth configuration changes to a major package version.

## 0.2.0

- Added `QuantumApiManager` for one Inspector configuration and shared client across scenes.
- Added manager context-menu health and random requests.
- Fixed the production API endpoint inside the client source and removed the base URL override.
- Added a Package Manager entry for the Basic Usage sample.

## 0.1.0

- Added Unity client, DTOs, coroutine and task requests, and basic sample code.
