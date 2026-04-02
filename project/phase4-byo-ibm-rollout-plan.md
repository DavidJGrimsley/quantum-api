# Phase 4 BYO IBM Rollout Plan

This document is the handoff for the Phase 4 V1 rollout across Quantum API, Identerest, and the portfolio site.

## Scope

Phase 4 V1 is a bring-your-own IBM credentials release.

- Users keep using Quantum API simulator features with their normal Quantum API key.
- Users who want IBM hardware features save their own IBM credentials to their account.
- Quantum API uses those saved credentials server-side when the same user later calls IBM-backed endpoints with an API key.
- Managed IBM resale is intentionally out of scope for this version.

This means your portfolio site can act like any other BYO user: sign in with Identerest, save an IBM profile, create a Quantum API key, and use that key for both simulator features and IBM-backed calls.

## Delivered In This Repo

The Quantum API backend now includes:

- bearer-authenticated IBM profile endpoints at `/v1/ibm/profiles*`
- API-key-authenticated IBM hardware job endpoints at `/v1/jobs*`
- per-user IBM profile resolution for `GET /v1/list_backends` and `POST /v1/transpile`
- encrypted IBM token storage with masked token metadata in responses
- poll-on-read async job tracking for IBM Runtime jobs

## Identerest Schema Work

Apply the updated Supabase schema script in:

- [`docs/operations/phase3_5_supabase_schema.sql`](/home/deployer/quantum-api/docs/operations/phase3_5_supabase_schema.sql)

New tables introduced for Phase 4 V1:

- `public.ibm_credential_profiles`
- `public.quantum_execution_jobs`

Server config required for stored IBM profiles:

- `IBM_CREDENTIAL_ENCRYPTION_KEY`

Important boundary:

- Portfolio and Identerest UI should call Quantum API endpoints.
- They should not write IBM secrets directly to Supabase tables.
- Quantum API remains responsible for validation, encryption, masking, and credential verification.

## Portfolio UI Workstream

Update the existing API key management area with a collapsible section titled `IBM Credentials`.

Expected UI capabilities:

- list saved IBM profiles
- add a new IBM profile
- edit name/token/instance/channel
- delete a profile
- set one profile as default
- run a verify action against the backend

Recommended fields inside the collapsible panel:

- `Profile name`
- `IBM API token`
- `IBM instance / CRN`
- `Channel`

Recommended default channel:

- `ibm_quantum_platform`

## Info Copy For The UI

Use an info icon or tooltip near the `IBM Credentials` heading with copy along these lines:

> IBM credentials are optional. Without them, your Quantum API key can still use simulator-backed endpoints. Add your own IBM credentials if you want backend discovery, transpilation, and async hardware jobs on IBM quantum systems through the same Quantum API account.

## API Integration Notes

The frontend should use bearer-authenticated Quantum API routes for IBM profile management:

- `GET /v1/ibm/profiles`
- `POST /v1/ibm/profiles`
- `PATCH /v1/ibm/profiles/{profile_id}`
- `DELETE /v1/ibm/profiles/{profile_id}`
- `POST /v1/ibm/profiles/{profile_id}/verify`

Hardware execution remains API-key based:

- `POST /v1/jobs/circuits`
- `GET /v1/jobs/{job_id}`
- `GET /v1/jobs/{job_id}/result`
- `POST /v1/jobs/{job_id}/cancel`

Key behavior:

- bearer JWT manages user-owned credentials
- Quantum API key identifies the owning user during runtime calls
- if an IBM profile name is omitted, Quantum API uses the owner's default saved profile

## Automated Live Verifier

Preferred live-smoke command:

```bash
export VERIFY_API_BASE_URL=https://davidjgrimsley.com/public-facing/api/quantum
export VERIFY_BEARER_JWT=<supabase_jwt>
export VERIFY_IBM_TOKEN=<ibm_api_token>
export VERIFY_IBM_INSTANCE=<ibm_instance_or_crn>
export VERIFY_IBM_CHANNEL=ibm_quantum_platform

uv run python scripts/verify_byo_ibm_flow.py --timeout-seconds 1800
```

Important notes:

- `VERIFY_API_BASE_URL` may be the service root or the full `/v1` URL. The verifier appends `/v1` when missing.
- Stored-profile verification requires `IBM_CREDENTIAL_ENCRYPTION_KEY` on the deployed Quantum API runtime.
- Use `--backend-name <backend>` if you want to force a specific IBM backend.
- The verifier cleans up the created key/profile by default. Use `--no-cleanup` if you need to inspect created rows afterward.
- Record the run date, environment, selected backend, terminal job status, result/error artifact, and cleanup outcome in release notes or `project/TODO.md`.

## Live Smoke Checklist

1. Sign in through Identerest on the portfolio site.
2. Expand `IBM Credentials`.
3. Save an IBM profile using a real token and instance.
4. Verify the profile successfully.
5. Create or reuse a Quantum API key.
6. Call `GET /v1/list_backends?provider=ibm`.
7. Call `POST /v1/transpile` with `provider=ibm` against one of the returned IBM backends.
8. Submit `POST /v1/jobs/circuits`.
9. Poll `GET /v1/jobs/{job_id}` until terminal.
10. Fetch `GET /v1/jobs/{job_id}/result` for `succeeded`, or capture the structured provider error from `GET /v1/jobs/{job_id}` for `failed` / `cancelled`.
11. Record date, environment, backend, terminal status, result/error artifact, and cleanup outcome.

## Deferred Managed IBM Access

If you later want Quantum API to resell IBM-backed access using your own provider account, add a separate workstream for:

- billing and plan enforcement
- quotas and abuse controls
- provider cost caps
- failed-job accounting
- legal and terms review for resale
