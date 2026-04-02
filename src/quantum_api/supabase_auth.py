from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx
import jwt
from jwt import InvalidTokenError, PyJWTError

from quantum_api.config import Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    email: str | None
    claims: dict[str, Any]


class JwtVerificationError(Exception):
    pass


class SupabaseJwtVerifier:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: httpx.AsyncClient | None = None
        self._client_loop: asyncio.AbstractEventLoop | None = None
        self._jwks_by_kid: dict[str, dict[str, Any]] = {}
        self._jwks_cached_at = 0.0
        self._lock: asyncio.Lock | None = None
        self._jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"

    async def startup_check(self) -> None:
        if not self._settings.auth_enabled:
            return
        await self._ensure_http_client()
        try:
            await self._refresh_jwks_if_needed(force=False)
        except Exception:
            if self._settings.is_production_like():
                raise
            logger.warning("Unable to prefetch Supabase JWKS during startup; will retry on demand.", exc_info=True)

    async def close(self) -> None:
        await self._discard_http_client()

    async def verify_authorization_header(self, authorization_header: str | None) -> AuthenticatedUser:
        token = self._extract_bearer_token(authorization_header)
        return await self.verify_token(token)

    async def verify_token(self, token: str) -> AuthenticatedUser:
        header = self._read_unverified_header(token)
        kid = str(header.get("kid", "")).strip()
        algorithm = str(header.get("alg", "RS256")).strip() or "RS256"
        if not kid:
            raise JwtVerificationError("Token is missing key identifier (kid).")

        key_jwk = await self._jwk_for_kid(kid)
        if key_jwk is None:
            # One forced refresh before failing hard for rotated keys.
            await self._refresh_jwks_if_needed(force=True)
            key_jwk = self._jwks_by_kid.get(kid)
            if key_jwk is None:
                raise JwtVerificationError("Token signing key is unknown.")

        try:
            public_key = jwt.PyJWK.from_dict(key_jwk).key
            claims = jwt.decode(
                token,
                key=public_key,
                algorithms=[algorithm],
                audience=self._settings.supabase_jwt_audience,
                issuer=self._settings.supabase_jwt_issuer_effective,
                options={"require": ["exp", "iat", "sub"]},
            )
        except PyJWTError as exc:
            raise JwtVerificationError("JWT validation failed.") from exc

        user_id = str(claims.get("sub", "")).strip()
        if not user_id:
            raise JwtVerificationError("JWT payload is missing a valid subject.")

        email_value = claims.get("email")
        email = str(email_value).strip() if isinstance(email_value, str) and email_value.strip() else None
        return AuthenticatedUser(user_id=user_id, email=email, claims=dict(claims))

    @staticmethod
    def _extract_bearer_token(authorization_header: str | None) -> str:
        if not authorization_header:
            raise JwtVerificationError("Missing Authorization header.")
        scheme, _, token = authorization_header.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise JwtVerificationError("Authorization header must be a bearer token.")
        return token.strip()

    @staticmethod
    def _read_unverified_header(token: str) -> dict[str, Any]:
        try:
            return jwt.get_unverified_header(token)
        except InvalidTokenError as exc:
            raise JwtVerificationError("Malformed JWT header.") from exc

    async def _jwk_for_kid(self, kid: str) -> dict[str, Any] | None:
        await self._refresh_jwks_if_needed(force=False)
        return self._jwks_by_kid.get(kid)

    async def _refresh_jwks_if_needed(self, *, force: bool) -> None:
        await self._ensure_http_client()
        now = time.time()
        if not force and self._jwks_by_kid and (now - self._jwks_cached_at) < self._settings.supabase_jwks_cache_seconds:
            return

        assert self._lock is not None
        async with self._lock:
            now = time.time()
            if (
                not force
                and self._jwks_by_kid
                and (now - self._jwks_cached_at) < self._settings.supabase_jwks_cache_seconds
            ):
                return

            assert self._client is not None
            response = await self._client.get(self._jwks_url)
            response.raise_for_status()
            payload = response.json()
            keys = payload.get("keys")
            if not isinstance(keys, list):
                raise JwtVerificationError("JWKS response did not include a valid keys array.")

            parsed: dict[str, dict[str, Any]] = {}
            for item in keys:
                if not isinstance(item, dict):
                    continue
                kid = str(item.get("kid", "")).strip()
                if not kid:
                    continue
                parsed[kid] = item

            if not parsed:
                raise JwtVerificationError("JWKS response did not include usable signing keys.")

            self._jwks_by_kid = parsed
            self._jwks_cached_at = now
            logger.info("Supabase JWKS cache refreshed with %s keys.", len(parsed))

    async def _ensure_http_client(self) -> None:
        current_loop = asyncio.get_running_loop()
        if (
            self._client is not None
            and not self._client.is_closed
            and self._client_loop is current_loop
            and self._lock is not None
        ):
            return

        if self._client is not None:
            await self._discard_http_client()

        self._client = httpx.AsyncClient(timeout=5.0)
        self._client_loop = current_loop
        self._lock = asyncio.Lock()

    async def _discard_http_client(self) -> None:
        client = self._client
        self._client = None
        self._client_loop = None
        self._lock = None
        if client is None:
            return
        try:
            await client.aclose()
        except RuntimeError:
            logger.debug("Unable to close Supabase JWKS HTTP client cleanly.", exc_info=True)
