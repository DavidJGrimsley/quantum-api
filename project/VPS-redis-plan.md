# Redis + Env Setup Plan (VPS, No Paid Redis)

This is the practical checklist for setting up these backend env vars on your VPS:

1. `DATABASE_URL`
2. `API_KEY_HASH_SECRET`
3. `SUPABASE_URL`
4. `SUPABASE_JWT_AUDIENCE`
5. `SUPABASE_JWT_ISSUER`
6. `REDIS_URL`

## Status Update (March 30, 2026)

- This plan is still valid for VPS deployment.
- `quantum-api` now supports Supabase JWT signing keys that use `ES256` (EC) or RSA-compatible JWKs.
- Local dev note: when `EXPO_PUBLIC_QUANTUM_API_BASE_URL=http://127.0.0.1:8000`, key-management routes under `/v1/*` are the target for Identerest login.
- The legacy portfolio metadata/demo routes (`/portfolio.json`, `/quantum_gate`) are not part of the new `/v1` key-management flow and can return `404` locally without blocking `/v1/keys`.

You do NOT need to pay another company for Redis. We will run Redis directly on your VPS.

## Hosting Policy (Important)

- Use self-hosted Redis on your VPS only.
- Do NOT use paid Redis hosting providers for this setup (for example: Upstash, Redis Cloud, ElastiCache, Memorystore).
- `REDIS_URL` should point to your VPS-local Redis instance (typically `redis://127.0.0.1:6379/0`).

---

## 0) Where this file applies

- Repo: `quantum-api`
- Server: your VPS
- File to fill: `.env` in the `quantum-api` project root

---

## 1) Get `SUPABASE_URL` (find it in dashboard)

Child version: this is your Supabase "home address."

How to find it:

1. Open Supabase dashboard.
2. Open your project.
3. Go to `Project Settings` -> `API`.
4. Copy `Project URL`.

Example:

```env
SUPABASE_URL=https://abcxyzcompany.supabase.co
```

---

## 2) Get `DATABASE_URL` (find/create)

Child version: this is where your app finds its notebook (database).

How to find/create:

1. In Supabase dashboard, open your project.
2. Go to `Project Settings` -> `Database`.
3. Find `Connection string` (URI form).
4. If password is unknown, reset it in Supabase first.
5. Copy URI and convert prefix to async driver for this app:
   - from `postgresql://...`
   - to `postgresql+asyncpg://...`

Example:

```env
DATABASE_URL=postgresql+asyncpg://postgres:<YOUR_DB_PASSWORD>@db.<PROJECT_REF>.supabase.co:5432/postgres?sslmode=require
```

---

## 3) Create `API_KEY_HASH_SECRET` (generate it on VPS)

Child version: secret spice. Never share it.

Generate it on VPS:

```bash
openssl rand -hex 32
```

Copy output into `.env`:

```env
API_KEY_HASH_SECRET=<PASTE_HEX_OUTPUT_HERE>
```

Alternative generator:

```bash
python3 - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
```

Important:

- Do not commit this into git.
- If leaked, rotate immediately.

---

## 4) Set `SUPABASE_JWT_AUDIENCE` (usually fixed)

Child version: who the ticket is for.

Use:

```env
SUPABASE_JWT_AUDIENCE=authenticated
```

For normal Supabase user sessions, `authenticated` is the correct value.

---

## 5) Set `SUPABASE_JWT_ISSUER` (easy option + explicit option)

Child version: who printed the ticket.

You have two valid choices:

1. Leave blank and let app derive it from `SUPABASE_URL`.
2. Set explicitly to:

```env
SUPABASE_JWT_ISSUER=https://<PROJECT_REF>.supabase.co/auth/v1
```

If you are unsure, leave it blank for now.

---

## 6) Install Redis on your VPS and set `REDIS_URL`

Child version: fast sticky-note memory for rate limits/cache.

### Ubuntu/Debian install

```bash
sudo apt update
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
sudo systemctl status redis-server --no-pager
```

Test it:

```bash
redis-cli ping
```

Expected:

```text
PONG
```

Set env:

```env
REDIS_URL=redis://127.0.0.1:6379/0
```

That means:

- `127.0.0.1`: same VPS machine
- `6379`: Redis port
- `/0`: first Redis DB bucket

### Optional hardening (later)

- Keep Redis bound to localhost only.
- Use firewall to block external Redis access.
- Add Redis password only if needed (extra ops overhead).

---

## 7) Full `.env` block (copy and fill)

```env
APP_ENV=production
AUTH_ENABLED=true

DATABASE_URL=postgresql+asyncpg://postgres:<YOUR_DB_PASSWORD>@db.<PROJECT_REF>.supabase.co:5432/postgres?sslmode=require
API_KEY_HASH_SECRET=<GENERATE_WITH_OPENSSL_RAND_HEX_32>

SUPABASE_URL=https://<PROJECT_REF>.supabase.co
SUPABASE_JWT_AUDIENCE=authenticated
SUPABASE_JWT_ISSUER=

REDIS_URL=redis://127.0.0.1:6379/0

# recommended prod settings
DATABASE_AUTO_CREATE=false
DEV_RATE_LIMIT_BYPASS=false
```

---

## 8) Quick verification commands on VPS

### Verify Redis

```bash
redis-cli -u "$REDIS_URL" ping
```

Expected: `PONG`

### Verify app can start with env

```bash
python3 -m pip install -e .[dev]
python3 -m pytest -q
```

### Run app

```bash
python3 -m uvicorn quantum_api.main:app --host 0.0.0.0 --port 8000
```

---

## 9) Common mistakes (avoid these)

1. Using `postgresql://` instead of `postgresql+asyncpg://` in `DATABASE_URL`.
2. Forgetting `?sslmode=require` for Supabase DB URL.
3. Putting `API_KEY_HASH_SECRET` in git.
4. Exposing Redis publicly to the internet.
5. Setting `DEV_RATE_LIMIT_BYPASS=true` in production.
