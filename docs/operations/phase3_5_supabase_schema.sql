-- Phase 3.5 schema for Supabase Postgres
-- Run in Supabase SQL editor (or migration tooling) before production rollout.

create extension if not exists pgcrypto;

create table if not exists public.api_keys (
  id uuid primary key default gen_random_uuid(),
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

create index if not exists idx_api_keys_owner_user_id on public.api_keys (owner_user_id);
create index if not exists idx_api_keys_status on public.api_keys (status);
create index if not exists idx_api_keys_key_hash_sha256 on public.api_keys (key_hash_sha256);
create index if not exists idx_api_keys_rotated_from_id on public.api_keys (rotated_from_id);
create index if not exists idx_api_keys_rotated_to_id on public.api_keys (rotated_to_id);

create table if not exists public.api_key_audit_events (
  id uuid primary key default gen_random_uuid(),
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

create index if not exists idx_api_key_audit_events_api_key_id on public.api_key_audit_events (api_key_id);
create index if not exists idx_api_key_audit_events_owner_user_id on public.api_key_audit_events (owner_user_id);
create index if not exists idx_api_key_audit_events_actor_user_id on public.api_key_audit_events (actor_user_id);
create index if not exists idx_api_key_audit_events_event_type on public.api_key_audit_events (event_type);

alter table public.api_keys enable row level security;
alter table public.api_key_audit_events enable row level security;

drop policy if exists api_keys_select_own on public.api_keys;
drop policy if exists api_keys_insert_own on public.api_keys;
drop policy if exists api_keys_update_own on public.api_keys;
drop policy if exists api_key_audit_events_select_own on public.api_key_audit_events;
drop policy if exists api_key_audit_events_insert_own on public.api_key_audit_events;

create policy api_keys_select_own on public.api_keys
  for select
  to authenticated
  using (owner_user_id = auth.uid()::text);

create policy api_keys_insert_own on public.api_keys
  for insert
  to authenticated
  with check (owner_user_id = auth.uid()::text);

create policy api_keys_update_own on public.api_keys
  for update
  to authenticated
  using (owner_user_id = auth.uid()::text)
  with check (owner_user_id = auth.uid()::text);

create policy api_key_audit_events_select_own on public.api_key_audit_events
  for select
  to authenticated
  using (owner_user_id = auth.uid()::text);

create policy api_key_audit_events_insert_own on public.api_key_audit_events
  for insert
  to authenticated
  with check (
    owner_user_id = auth.uid()::text
    and actor_user_id = auth.uid()::text
  );

grant select, insert, update on public.api_keys to authenticated;
grant select, insert on public.api_key_audit_events to authenticated;

-- Note on Supabase "automatic RLS":
-- New tables may default to RLS enabled depending on your project settings,
-- but owner-scoped policies like the above are still required.
