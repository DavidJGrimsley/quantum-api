from __future__ import annotations

import asyncio
import hmac
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from quantum_api.config import Settings
from quantum_api.key_management import (
    ApiKeyLifecycleService,
    KeyPolicy,
    RuntimeApiKey,
    parse_api_key_prefix,
)

logger = logging.getLogger(__name__)

_RATE_LIMIT_LUA = """
local second_key = KEYS[1]
local minute_key = KEYS[2]
local day_key = KEYS[3]

local second_limit = tonumber(ARGV[1])
local minute_limit = tonumber(ARGV[2])
local day_limit = tonumber(ARGV[3])
local second_ttl = tonumber(ARGV[4])
local minute_ttl = tonumber(ARGV[5])
local day_ttl = tonumber(ARGV[6])

local function current_count(key)
  local value = redis.call("GET", key)
  if not value then
    return 0
  end
  return tonumber(value)
end

local second_count = current_count(second_key)
if second_count + 1 > second_limit then
  local ttl = redis.call("TTL", second_key)
  if ttl < 0 then
    ttl = second_ttl
  end
  return {0, "second", second_limit, 0, ttl}
end

local minute_count = current_count(minute_key)
if minute_count + 1 > minute_limit then
  local ttl = redis.call("TTL", minute_key)
  if ttl < 0 then
    ttl = minute_ttl
  end
  return {0, "minute", minute_limit, 0, ttl}
end

local day_count = current_count(day_key)
if day_count + 1 > day_limit then
  local ttl = redis.call("TTL", day_key)
  if ttl < 0 then
    ttl = day_ttl
  end
  return {0, "daily", day_limit, 0, ttl}
end

local second_after = redis.call("INCR", second_key)
if redis.call("TTL", second_key) < 0 then
  redis.call("EXPIRE", second_key, second_ttl)
end

local minute_after = redis.call("INCR", minute_key)
if redis.call("TTL", minute_key) < 0 then
  redis.call("EXPIRE", minute_key, minute_ttl)
end

redis.call("INCR", day_key)
if redis.call("TTL", day_key) < 0 then
  redis.call("EXPIRE", day_key, day_ttl)
end

local minute_remaining = minute_limit - minute_after
if minute_remaining < 0 then
  minute_remaining = 0
end

return {1, "minute", minute_limit, minute_remaining, minute_ttl}
"""


class RateLimiterUnavailableError(Exception):
    """Raised when Redis-backed limiting cannot be evaluated."""


@dataclass(frozen=True)
class AuthenticatedApiKey:
    key_id: str
    owner_user_id: str
    key_prefix: str
    policy: KeyPolicy


@dataclass(frozen=True)
class ApiKeyAuthenticationAttempt:
    key: AuthenticatedApiKey | None
    failure_reason: str | None
    key_prefix: str | None


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    reason: str
    retry_after_seconds: int
    headers: dict[str, str]


class ApiKeyAuthService:
    def __init__(self, settings: Settings, lifecycle_service: ApiKeyLifecycleService) -> None:
        self._settings = settings
        self._lifecycle_service = lifecycle_service
        self._redis: Any | None = None
        self._redis_loop: asyncio.AbstractEventLoop | None = None

    async def startup_check(self) -> None:
        if not self._settings.redis_url.strip():
            return
        await self._ensure_cache_connection()
        try:
            assert self._redis is not None
            await self._redis.ping()
        except RedisError:
            logger.warning("API key metadata cache is unavailable; falling back to DB lookups.")
            await self._discard_redis()

    async def close(self) -> None:
        await self._discard_redis()

    async def authenticate(self, raw_api_key: str | None) -> AuthenticatedApiKey | None:
        attempt = await self.authenticate_with_diagnostics(raw_api_key)
        return attempt.key

    async def authenticate_with_diagnostics(self, raw_api_key: str | None) -> ApiKeyAuthenticationAttempt:
        if not raw_api_key:
            return ApiKeyAuthenticationAttempt(key=None, failure_reason="missing_header", key_prefix=None)

        prefix = parse_api_key_prefix(raw_api_key, key_format_prefix=self._settings.api_key_format_prefix)
        if prefix is None:
            return ApiKeyAuthenticationAttempt(key=None, failure_reason="invalid_format", key_prefix=None)

        runtime_key = await self._runtime_key_by_prefix(prefix=prefix)
        if runtime_key is None:
            return ApiKeyAuthenticationAttempt(key=None, failure_reason="unknown_prefix", key_prefix=prefix)

        candidate_hash = self._lifecycle_service.hash_raw_key(raw_api_key)
        if hmac.compare_digest(candidate_hash, runtime_key.key_hash_sha256):
            return ApiKeyAuthenticationAttempt(
                key=AuthenticatedApiKey(
                    key_id=runtime_key.key_id,
                    owner_user_id=runtime_key.owner_user_id,
                    key_prefix=runtime_key.key_prefix,
                    policy=runtime_key.policy,
                ),
                failure_reason=None,
                key_prefix=runtime_key.key_prefix,
            )

        return ApiKeyAuthenticationAttempt(key=None, failure_reason="hash_mismatch", key_prefix=prefix)

    async def invalidate_key_prefix(self, prefix: str) -> None:
        if not await self._ensure_cache_connection():
            return
        try:
            assert self._redis is not None
            await self._redis.delete(self._cache_key(prefix))
        except RedisError:
            logger.warning("Unable to invalidate API key metadata cache.", exc_info=True)

    async def _runtime_key_by_prefix(self, *, prefix: str) -> RuntimeApiKey | None:
        cached = await self._read_cache(prefix=prefix)
        if cached is not None:
            return cached

        runtime_key = await self._lifecycle_service.find_active_runtime_key_by_prefix(prefix=prefix)
        if runtime_key is not None:
            await self._write_cache(runtime_key)
        return runtime_key

    async def _read_cache(self, *, prefix: str) -> RuntimeApiKey | None:
        if not await self._ensure_cache_connection():
            return None
        try:
            assert self._redis is not None
            raw = await self._redis.get(self._cache_key(prefix))
        except RedisError:
            logger.warning("Unable to read API key metadata cache.", exc_info=True)
            return None
        if not raw:
            return None

        try:
            payload = json.loads(raw)
            policy = payload["policy"]
            return RuntimeApiKey(
                key_id=str(payload["key_id"]),
                owner_user_id=str(payload["owner_user_id"]),
                key_prefix=str(payload["key_prefix"]),
                key_hash_sha256=str(payload["key_hash_sha256"]),
                policy=KeyPolicy(
                    rate_limit_per_second=int(policy["rate_limit_per_second"]),
                    rate_limit_per_minute=int(policy["rate_limit_per_minute"]),
                    daily_quota=int(policy["daily_quota"]),
                ),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            logger.warning("Cached API key metadata payload is invalid.", exc_info=True)
            return None

    async def _write_cache(self, runtime_key: RuntimeApiKey) -> None:
        if not await self._ensure_cache_connection():
            return
        payload = json.dumps(
            {
                "key_id": runtime_key.key_id,
                "owner_user_id": runtime_key.owner_user_id,
                "key_prefix": runtime_key.key_prefix,
                "key_hash_sha256": runtime_key.key_hash_sha256,
                "policy": {
                    "rate_limit_per_second": runtime_key.policy.rate_limit_per_second,
                    "rate_limit_per_minute": runtime_key.policy.rate_limit_per_minute,
                    "daily_quota": runtime_key.policy.daily_quota,
                },
            }
        )
        try:
            assert self._redis is not None
            await self._redis.set(self._cache_key(runtime_key.key_prefix), payload, ex=self._settings.api_key_cache_ttl_seconds)
        except RedisError:
            logger.warning("Unable to write API key metadata cache.", exc_info=True)

    def _cache_key(self, prefix: str) -> str:
        return f"api-key-meta:{prefix}"

    async def _ensure_cache_connection(self) -> bool:
        current_loop = asyncio.get_running_loop()
        if self._redis is not None and self._redis_loop is current_loop:
            return True
        if self._redis is not None:
            await self._discard_redis()
        if not self._settings.redis_url.strip():
            return False
        self._redis = Redis.from_url(self._settings.redis_url, decode_responses=True)
        self._redis_loop = current_loop
        return True

    async def _discard_redis(self) -> None:
        redis = self._redis
        self._redis = None
        self._redis_loop = None
        if redis is None:
            return
        try:
            await redis.aclose()
        except (RedisError, RuntimeError):
            logger.debug("Unable to close API key metadata cache client cleanly.", exc_info=True)


class RedisRateLimiter:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._redis: Any | None = None
        self._redis_loop: asyncio.AbstractEventLoop | None = None

    async def startup_check(self) -> None:
        if not self._settings.rate_limiting_enabled:
            return

        if self._settings.app_env_normalized == "development" and self._settings.dev_rate_limit_bypass:
            return

        await self._ensure_redis_connection()
        try:
            assert self._redis is not None
            await self._redis.ping()
        except RedisError as exc:
            raise RateLimiterUnavailableError("Unable to ping Redis during startup") from exc

    async def close(self) -> None:
        await self._discard_redis()

    async def check_key(self, *, key_id: str, policy: KeyPolicy) -> RateLimitResult:
        result = await self._evaluate_limit(
            scope="key",
            identifier=key_id,
            second_limit=policy.rate_limit_per_second,
            minute_limit=policy.rate_limit_per_minute,
            day_limit=policy.daily_quota,
        )
        return self._with_scope_reason(result, "key")

    async def check_ip(self, client_ip: str) -> RateLimitResult:
        result = await self._evaluate_limit(
            scope="ip",
            identifier=client_ip,
            second_limit=self._settings.ip_rate_limit_per_second,
            minute_limit=self._settings.ip_rate_limit_per_minute,
            day_limit=max(self._settings.ip_rate_limit_per_minute * 200, 1),
        )
        return self._with_scope_reason(result, "ip")

    async def _evaluate_limit(
        self,
        *,
        scope: str,
        identifier: str,
        second_limit: int,
        minute_limit: int,
        day_limit: int,
    ) -> RateLimitResult:
        await self._ensure_redis_connection()
        assert self._redis is not None

        second_key, minute_key, day_key, second_ttl, minute_ttl, day_ttl = self._build_window_values(
            scope=scope,
            identifier=identifier,
        )

        try:
            raw_result: list[Any] = await self._redis.eval(
                _RATE_LIMIT_LUA,
                3,
                second_key,
                minute_key,
                day_key,
                second_limit,
                minute_limit,
                day_limit,
                second_ttl,
                minute_ttl,
                day_ttl,
            )
        except RedisError as exc:
            raise RateLimiterUnavailableError("Unable to evaluate Redis rate limit") from exc

        allowed = bool(int(raw_result[0]))
        window = str(raw_result[1])
        limit = int(raw_result[2])
        remaining = max(int(raw_result[3]), 0)
        reset_seconds = max(int(raw_result[4]), 1)

        headers = {
            "RateLimit-Limit": str(limit),
            "RateLimit-Remaining": str(remaining),
            "RateLimit-Reset": str(reset_seconds),
        }

        return RateLimitResult(
            allowed=allowed,
            reason=window,
            retry_after_seconds=reset_seconds,
            headers=headers,
        )

    async def _ensure_redis_connection(self) -> None:
        current_loop = asyncio.get_running_loop()
        if self._redis is not None and self._redis_loop is current_loop:
            return
        if self._redis is not None:
            await self._discard_redis()
        if not self._settings.redis_url.strip():
            raise RateLimiterUnavailableError("REDIS_URL is empty")
        self._redis = Redis.from_url(self._settings.redis_url, decode_responses=True)
        self._redis_loop = current_loop

    def _build_window_values(
        self, *, scope: str, identifier: str
    ) -> tuple[str, str, str, int, int, int]:
        now = datetime.now(UTC)
        epoch_second = int(now.timestamp())
        epoch_minute = epoch_second // 60
        day_bucket = now.strftime("%Y%m%d")

        next_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        next_day = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

        second_ttl = 2
        minute_ttl = max(int((next_minute - now).total_seconds()), 1)
        day_ttl = max(int((next_day - now).total_seconds()), 1)

        second_key = f"rate:{scope}:{identifier}:second:{epoch_second}"
        minute_key = f"rate:{scope}:{identifier}:minute:{epoch_minute}"
        day_key = f"quota:{scope}:{identifier}:day:{day_bucket}"
        return second_key, minute_key, day_key, second_ttl, minute_ttl, day_ttl

    async def _discard_redis(self) -> None:
        redis = self._redis
        self._redis = None
        self._redis_loop = None
        if redis is None:
            return
        try:
            await redis.aclose()
        except (RedisError, RuntimeError):
            logger.debug("Unable to close Redis rate limiter client cleanly.", exc_info=True)

    @staticmethod
    def _with_scope_reason(result: RateLimitResult, scope: str) -> RateLimitResult:
        return RateLimitResult(
            allowed=result.allowed,
            reason=f"{scope}_{result.reason}",
            retry_after_seconds=result.retry_after_seconds,
            headers=result.headers,
        )
