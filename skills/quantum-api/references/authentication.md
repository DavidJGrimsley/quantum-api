# Quantum API — Authentication Guide

---

## ?? Administrative Endpoints Only

> [!IMPORTANT]
> **Agents must never attempt to create, manage, or rotate API keys or IBM profiles.** The /v1/keys and /v1/ibm/profiles endpoints are strictly for administrative use by the system owner (David). When integrating the API, ask the user to provide their X-API-Key directly.

## Two Auth Modes

The Quantum API uses two completely separate auth systems for different endpoint groups:

| Auth mode | Header | Used for |
|---|---|---|
| **Supabase Bearer JWT** | `Authorization: Bearer <jwt>` | Key management (`/v1/keys*`), IBM profiles (`/v1/ibm/profiles*`) |
| **API Key** | `X-API-Key: <key>` | All other runtime `/v1/*` endpoints |

**Public endpoints** (no auth): `GET /v1/health`, `GET /v1/portfolio.json`, `GET /v1/echo-types`.

---

## Obtaining a Supabase JWT

The Supabase JWT is obtained from the Identerest/portfolio Supabase project. This is the user's **login session token** — it is not the same as an API key. It is used only to manage keys and IBM profiles, not to call runtime endpoints.

For self-hosted or local development, configure `SUPABASE_URL`, `SUPABASE_JWT_AUDIENCE`, and `SUPABASE_JWT_ISSUER` in `.env`. The service validates JWTs against the Supabase JWKS endpoint.

---

## API Key Lifecycle

### Creating a Key

```http
POST /v1/keys
Authorization: Bearer <supabase_jwt>
Content-Type: application/json

{}
```

The response includes the **raw key exactly once**. Store it immediately — it cannot be retrieved again.

```json
{
  "key_id": "...",
  "key": "qapi_...",
  "created_at": "..."
}
```

### Using a Key

```http
GET /v1/circuits/run
X-API-Key: qapi_your_key_here
```

### Rotating a Key

```http
POST /v1/keys/{key_id}/rotate
Authorization: Bearer <supabase_jwt>
```

The old key becomes invalid immediately. The response returns the new raw key (shown once only).

### Revoking a Key

```http
POST /v1/keys/{key_id}/revoke
Authorization: Bearer <supabase_jwt>
```

Revoked keys are retained in history. To delete them permanently:

```http
DELETE /v1/keys/{key_id}          # one revoked key
DELETE /v1/keys/revoked            # all revoked keys for this user
```

### Listing Keys

```http
GET /v1/keys
Authorization: Bearer <supabase_jwt>
```

Returns masked metadata only — never raw key values.

### Limits

| Limit | Config key | Default |
|---|---|---|
| Max active keys per user | `MAX_ACTIVE_API_KEYS_PER_USER` | server-configured |
| Max total key history per user | `MAX_TOTAL_API_KEYS_PER_USER` | server-configured |

---

## IBM Credential Profiles

IBM profiles store encrypted BYO IBM Quantum credentials so users can submit jobs to real IBM hardware without embedding tokens in API calls.

### Saving a Profile

```http
POST /v1/ibm/profiles
Authorization: Bearer <supabase_jwt>
Content-Type: application/json

{
  "profile_name": "my-open-plan",
  "token": "ibm_api_token_here",
  "instance": "crn:v1:bluemix:public:quantum-computing:us-east:...",
  "channel": "ibm_quantum_platform",
  "is_default": true
}
```

- `profile_name` must be unique per user.
- `channel` defaults to `ibm_quantum_platform`.
- Raw tokens are **write-only**. Subsequent reads return masked metadata only.
- Requires `IBM_CREDENTIAL_ENCRYPTION_KEY` on the server.

### Verifying a Profile

```http
POST /v1/ibm/profiles/{profile_id}/verify
Authorization: Bearer <supabase_jwt>
```

Performs a live IBM Runtime lookup and persists the status as `verified` or `invalid`.

### Using a Profile in Runtime Calls

Pass `ibm_profile: "my-open-plan"` in the request body of:
- `GET /v1/list_backends` (query param `ibm_profile`)
- `POST /v1/transpile`
- `POST /v1/jobs/circuits`
- `POST /v1/jobs/qasm`

If omitted, the API uses the owner's default saved profile.

---

## Development / Local Keys

For local development with the default `.env.example` values, use:

```
X-API-Key: qapi_devlocal_0123456789abcdef0123456789abcdef
```

**Never use dev keys in production.** The server will reject dev keys when `APP_ENV` is not `development`.

---

## Server-Level IBM Fallback

If no stored BYO profile is available, the server falls back to its own `IBM_TOKEN` and `IBM_INSTANCE` environment variables. This is a self-host/local fallback — not available in the production multi-tenant environment.

