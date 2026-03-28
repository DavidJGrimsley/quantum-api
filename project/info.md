# Project Info - Quantum API

## Product Goal

Build a production-ready, open source Quantum API backend that exposes a clean `/v1` contract for quantum gate execution and text transformation.

## Primary Consumers

1. Godot text adventure game (`choose-your-own-quantum-adventure-(4.4)/` in upstream repo)
2. Expo/React Native animation component (`text-adventure/` in upstream repo)
3. Unreal Engine runtime clients (planned)
4. Unity runtime clients (planned)
5. Future third-party clients through SDKs

## Scope (Phase 1)

- Greenfield FastAPI backend with no backward compatibility routes
- Core endpoints:
  - `GET /v1/health`
  - `GET /v1/echo-types`
  - `POST /v1/gates/run`
  - `POST /v1/text/transform`
- Strict validation, bounded input size, timeout middleware, sanitized errors
- CI, Docker, README, and migration docs
- JS and Python SDK scaffolds

## Out of Scope (Phase 1)

- Legacy route aliases
- Authentication and rate limiting
- Async job queue execution model
- Domain-specific algorithm APIs (finance/ML/optimization)

## Constraints

- Keep API contract stable and explicit
- Prefer typed models over unstructured payloads
- Keep qiskit optional at runtime while still exposing availability status
- Avoid hardcoded production URLs in server runtime code

## Success Criteria

- Endpoints respond according to contract with tests passing
- CI validates lint, tests, package build, and docker build
- Migration docs are implementation-ready for both external consumers
- Repository docs are clear enough for a new contributor to onboard quickly
