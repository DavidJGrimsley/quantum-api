from __future__ import annotations

import hashlib
import hmac
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from quantum_api.config import ApiKeyPolicy, Settings

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
    policy: ApiKeyPolicy


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    reason: str
    retry_after_seconds: int
    headers: dict[str, str]


class ApiKeyAuthService:
    def __init__(self, settings: Settings) -> None:
        self._enabled_policies = [policy for policy in settings.parsed_api_keys() if policy.enabled]

    def authenticate(self, raw_api_key: str | None) -> AuthenticatedApiKey | None:
        if not raw_api_key:
            return None

        candidate_hash = hashlib.sha256(raw_api_key.encode("utf-8")).hexdigest()
        for policy in self._enabled_policies:
            if hmac.compare_digest(candidate_hash, policy.key_hash_sha256):
                return AuthenticatedApiKey(key_id=policy.key_id, policy=policy)

        return None


class RedisRateLimiter:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._redis: Redis | None = None

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
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None

    async def check_key(self, policy: ApiKeyPolicy) -> RateLimitResult:
        result = await self._evaluate_limit(
            scope="key",
            identifier=policy.key_id,
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
        if self._redis is not None:
            return
        if not self._settings.redis_url.strip():
            raise RateLimiterUnavailableError("REDIS_URL is empty")
        self._redis = Redis.from_url(self._settings.redis_url, decode_responses=True)

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

    @staticmethod
    def _with_scope_reason(result: RateLimitResult, scope: str) -> RateLimitResult:
        return RateLimitResult(
            allowed=result.allowed,
            reason=f"{scope}_{result.reason}",
            retry_after_seconds=result.retry_after_seconds,
            headers=result.headers,
        )
