# Phase 3.75 Cutover Checklist (Identerest Login + Quantum API Keys)

This checklist is the release gate for shipping Phase 3 -> 3.5 -> 3.75 as a complete slice.

## 1) Infrastructure Gate

- [x] Identerest Supabase migration applied (`api_keys`, `api_key_audit_events`).
- [x] RLS enabled on both tables.
- [x] Owner-scoped policies present for `authenticated` users.
- [x] Quantum API points at Supabase Postgres (`DATABASE_URL` with SSL).
- [x] `DATABASE_AUTO_CREATE=false` in non-local environments.
- [x] Redis available for rate limiting (`REDIS_URL`) or acceptable fallback behavior acknowledged.

## 2) Auth and Contract Gate

- [x] JWT bearer auth required for `/v1/keys*`.
- [x] `X-API-Key` runtime auth unchanged for non-key endpoints.
- [x] Endpoint contracts unchanged:
  - `GET /v1/keys`
  - `POST /v1/keys`
  - `DELETE /v1/keys/{key_id}`
  - `DELETE /v1/keys/revoked`
  - `POST /v1/keys/{key_id}/revoke`
  - `POST /v1/keys/{key_id}/rotate`

## 3) Safety Guardrail Gate

- [x] Active key cap enforced (`MAX_ACTIVE_API_KEYS_PER_USER`).
- [x] Total key history cap enforced (`MAX_TOTAL_API_KEYS_PER_USER`).
- [x] Revoked-key cleanup endpoints available for user hygiene.
- [x] One-time raw secret reveal behavior preserved.

## 4) Verification Gate

- [x] Lifecycle verification executed on March 31, 2026:
  - create key -> auth success
  - rotate key -> old key rejected, new key accepted
  - revoke key -> revoked key rejected
  - audit event coverage present (`create`, `rotate`, `revoke`)
- [x] Verification details recorded in this cutover checklist/release docs.

## 5) Rollback and Recovery

If rollout issues appear:

1. Keep migration in place (no destructive rollback on key tables).
2. Roll Quantum API deployment back to previous known-good image.
3. Confirm env parity (`SUPABASE_URL`, `SUPABASE_JWT_*`, `DATABASE_URL`, `API_KEY_HASH_SECRET`, `REDIS_URL`).
4. Re-run lifecycle verification script to isolate config vs code regression.
5. If needed, temporarily lock new key creation by reducing limits or adding maintenance banner in Portfolio while preserving read/revoke paths.
