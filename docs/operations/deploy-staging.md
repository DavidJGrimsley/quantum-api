# Staging Deployment Playbook

## Preflight

1. Confirm image tag is built and available.
2. Confirm Redis is reachable from staging runtime network.
3. Confirm staging secrets are set: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_JWT_AUDIENCE`, `REDIS_URL`, and `METRICS_TOKEN`.
4. If staging is validating BYO IBM rollout, also confirm `IBM_CREDENTIAL_ENCRYPTION_KEY` is set on the API runtime.
5. Confirm `APP_ENV=staging` and `ALLOW_ORIGINS` is explicit (no `*`).

## Deploy

1. Roll out new image to staging with `AUTH_ENABLED=true` and `RATE_LIMITING_ENABLED=true`.
2. Verify startup health and logs for Redis startup check success.
3. Run smoke tests:
   - `GET /v1/health` without API key returns `200`.
   - `GET /v1/echo-types` without API key returns `401`.
   - `GET /v1/echo-types` with a DB-backed Quantum API key returns `200` and `RateLimit-*` headers.
   - `GET /metrics` without metrics token returns `401`.
   - `GET /metrics` with metrics token returns `200`.
4. If this release includes BYO IBM rollout validation, run `uv run python scripts/verify_byo_ibm_flow.py ...` with a real bearer JWT and real IBM credentials after the general smoke checks pass.

## Post-deploy Verification

1. Confirm `quantum_api_http_requests_total` increments.
2. Confirm `quantum_api_auth_failures_total` increments for invalid API key test.
3. Confirm no sustained 5xx increase after rollout.

## Rollback

1. Revert to previous known-good image.
2. Keep Redis and keys unchanged unless incident analysis requires key revocation.
3. Re-run smoke tests and verify recovery metrics.
