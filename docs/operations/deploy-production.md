# Production Deployment Playbook

## Preflight

1. Promote only artifacts validated in staging.
2. Confirm production secrets and policies:
   - `APP_ENV=production`
   - explicit `ALLOW_ORIGINS`
   - `AUTH_ENABLED=true`
   - `RATE_LIMITING_ENABLED=true`
   - `DEV_RATE_LIMIT_BYPASS=false`
   - valid `REDIS_URL`
   - valid `METRICS_TOKEN`
   - `IBM_CREDENTIAL_ENCRYPTION_KEY` if BYO IBM stored-profile routes are enabled in this rollout
3. Confirm alert rules from `docs/operations/alerts.prometheus.yml` are loaded.

## Canary Rollout

1. Route 10% of traffic to the new version.
2. Hold for 15 minutes.
3. Verify:
   - no alert firing for 5xx or latency
   - stable in-flight levels
   - expected auth and rate-limit counters

## Full Rollout

1. Increase traffic to 50%, then 100%.
2. Re-run smoke checks:
   - public health endpoint
   - protected endpoint with and without a DB-backed Quantum API key
   - metrics endpoint with and without metrics token
   - if validating BYO IBM rollout, run `uv run python scripts/verify_byo_ibm_flow.py ...` with a real bearer JWT and real IBM credentials

## Incident and Rollback

1. Roll back immediately if:
   - `5xx rate > 1% for 10m`
   - p95 latency violates SLO for 10m
   - Redis unavailability causes sustained `503` responses
2. Capture request IDs from failing responses for log correlation.
3. After rollback, keep protections enabled unless outage root cause is policy misconfiguration.
