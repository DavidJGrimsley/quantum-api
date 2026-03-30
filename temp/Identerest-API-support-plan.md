# Identerest API Support Plan (Monorepo Import)

This plan replaces any prior portfolio-host-specific migration targeting.
All auth + key-management schema work should run in the **Identerest Supabase project**.

## Goal

Use a shared "Identerest Account" identity/data project for:

1. Supabase Auth (magic link + GitHub)
2. Quantum API key lifecycle storage (`api_keys`, `api_key_audit_events`)
3. Future multi-app account reuse

Redis stays self-hosted on your VPS (no paid Redis hosting).

## Architecture Decision

1. Supabase project: `Identerest` (auth + Postgres)
2. Quantum API backend:
   - `SUPABASE_URL` -> Identerest Supabase URL
   - `DATABASE_URL` -> Identerest Postgres connection string
   - `REDIS_URL` -> VPS local Redis (`redis://127.0.0.1:6379/0`)
3. Portfolio frontend:
   - uses Identerest-branded login copy/UI
   - still calls Quantum API key-management endpoints

## Identerest Monorepo Tasks

1. Add migration file in Identerest repo (example path):
   - `supabase/migrations/20260330_quantum_api_key_management.sql`
2. Apply migration to Identerest Supabase DB.
3. Enable auth providers in Identerest Supabase:
   - Email magic link
   - GitHub OAuth
4. Add allowed redirect URLs for each consuming app (Portfolio, etc.).
5. Add a short Identerest "Account" page that explains shared sign-in across apps.

## SQL Migration (Run Against Identerest Supabase)

```sql
-- 20260330_quantum_api_key_management.sql
-- Target: Identerest Supabase project

create extension if not exists pgcrypto;

create table if not exists public.api_keys (
  id uuid primary key default gen_random_uuid(),
  app_scope text not null default 'quantum-api',
  owner_user_id text not null,
  name text null,
  key_prefix text not null unique,
  key_hash_sha256 text not null,
  status text not null default 'active',
  rate_limit_per_second integer not null,
  rate_limit_per_minute integer not null,
  daily_quota integer not null,
  created_at timestamptz not null default now(),
  revoked_at timestamptz null,
  rotated_from_id uuid null,
  rotated_to_id uuid null,
  last_used_at timestamptz null,
  constraint api_keys_status_check check (status in ('active', 'revoked', 'rotated')),
  constraint api_keys_rate_limit_minute_check check (rate_limit_per_minute >= rate_limit_per_second)
);

create index if not exists idx_api_keys_app_scope on public.api_keys (app_scope);
create index if not exists idx_api_keys_owner_user_id on public.api_keys (owner_user_id);
create index if not exists idx_api_keys_status on public.api_keys (status);
create index if not exists idx_api_keys_key_hash_sha256 on public.api_keys (key_hash_sha256);
create index if not exists idx_api_keys_rotated_from_id on public.api_keys (rotated_from_id);
create index if not exists idx_api_keys_rotated_to_id on public.api_keys (rotated_to_id);

create table if not exists public.api_key_audit_events (
  id uuid primary key default gen_random_uuid(),
  app_scope text not null default 'quantum-api',
  api_key_id uuid not null references public.api_keys(id) on delete cascade,
  owner_user_id text not null,
  actor_user_id text not null,
  event_type text not null,
  event_metadata jsonb null,
  created_at timestamptz not null default now(),
  ip_address text null,
  user_agent text null,
  constraint api_key_audit_events_type_check check (event_type in ('create', 'revoke', 'rotate'))
);

create index if not exists idx_api_key_audit_events_app_scope on public.api_key_audit_events (app_scope);
create index if not exists idx_api_key_audit_events_api_key_id on public.api_key_audit_events (api_key_id);
create index if not exists idx_api_key_audit_events_owner_user_id on public.api_key_audit_events (owner_user_id);
create index if not exists idx_api_key_audit_events_actor_user_id on public.api_key_audit_events (actor_user_id);
create index if not exists idx_api_key_audit_events_event_type on public.api_key_audit_events (event_type);
```

## Quantum API Env Mapping (Point To Identerest)

```env
APP_ENV=production
AUTH_ENABLED=true

DATABASE_URL=postgresql+asyncpg://postgres:<PASSWORD>@db.<IDENTEREST_PROJECT_REF>.supabase.co:5432/postgres?sslmode=require
API_KEY_HASH_SECRET=<openssl rand -hex 32>

SUPABASE_URL=https://<IDENTEREST_PROJECT_REF>.supabase.co
SUPABASE_JWT_AUDIENCE=authenticated
SUPABASE_JWT_ISSUER=

REDIS_URL=redis://127.0.0.1:6379/0
DATABASE_AUTO_CREATE=false
DEV_RATE_LIMIT_BYPASS=false
```

## Rollout Sequence

1. Apply Identerest migration SQL.
2. Configure Identerest auth providers + redirects.
3. Set Quantum API envs to Identerest project + VPS Redis.
4. Restart Quantum API.
5. Verify:
   - login works from portfolio
   - `GET /v1/keys` works with bearer token
   - create/revoke/rotate persist in Identerest DB
   - protected runtime endpoints still enforce `X-API-Key`

## Notes / Risks

1. Shared auth is intentional: users sign into Identerest Account even if they came from Portfolio.
2. `app_scope` defaults to `quantum-api`; later apps can reuse the same tables safely.
3. No paid Redis provider is needed; keep Redis local to VPS and not publicly exposed.
