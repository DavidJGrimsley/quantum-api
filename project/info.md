# Project Info - Quantum API

## Product Goal

Run a production-ready Quantum API that supports:

1. public quantum compute endpoints (`/v1/*`)
2. user-scoped API key lifecycle management (`/v1/keys*`)
3. portfolio self-serve onboarding through Identerest Account auth

## Current State (Phase 3, 3.5, 3.75)

- Phase 1 and 2 endpoint surface is delivered (`/circuits`, `/transpile`, `/qasm`, backend discovery).
- Phase 3 security hardening is delivered:
  - JWT bearer auth for key-management routes
  - `X-API-Key` runtime auth for protected execution routes
  - Redis-backed rate limiting + quotas
  - structured metrics/logging
- Phase 3.5 key lifecycle is delivered:
  - `GET /v1/keys`
  - `POST /v1/keys`
  - `DELETE /v1/keys/{key_id}` (revoked-only permanent delete)
  - `DELETE /v1/keys/revoked` (bulk permanent delete for revoked keys)
  - `POST /v1/keys/{key_id}/revoke`
  - `POST /v1/keys/{key_id}/rotate`
- Phase 3.75 rollout alignment is in progress:
  - Identerest Supabase migration script hardened (`pgcrypto` + explicit RLS policies)
  - docs aligned to Identerest auth/key rollout flow
  - active key cap now enforced (`MAX_ACTIVE_API_KEYS_PER_USER`, default `5`)
  - total key-history cap now enforced (`MAX_TOTAL_API_KEYS_PER_USER`, default `100`)
  - JWT verifier now accepts Supabase ES256 JWKS signing keys
  - runtime DB config switched to Supabase Postgres in `.env` (`postgresql+asyncpg`, `DATABASE_AUTO_CREATE=false`)
  - live verification confirms `api_keys` + `api_key_audit_events` tables exist with RLS enabled and policies present

## Scope (Current Session)

- Keep key endpoint contracts unchanged.
- Keep auth split unchanged:
  - bearer JWT for `/v1/keys*`
  - `X-API-Key` for other protected `/v1/*`
- Keep schema aligned with runtime ORM (`api_keys`, `api_key_audit_events`) without introducing `app_scope`.
- Align rollout docs and operational checklists to Identerest as the active auth/data project.

## Constraints

- Production/staging must run with `DATABASE_AUTO_CREATE=false`.
- Supabase JWT issuer/audience validation must stay strict.
- Redis remains required for production rate limiting.
- RLS must be explicit: project-level “automatic RLS” does not replace owner-scoped policy definitions.

## Success Criteria

- Migration SQL applies cleanly in Identerest Supabase.
- Portfolio-authenticated key lifecycle calls succeed end-to-end.
- Revoked/rotated keys are rejected on runtime `X-API-Key` routes.
- Project docs accurately reflect delivered behavior and remaining backlog.
