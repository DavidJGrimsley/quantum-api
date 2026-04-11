from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import string
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, Uuid, delete, func, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from quantum_api.config import Settings

logger = logging.getLogger(__name__)

_ALPHABET = string.ascii_lowercase + string.digits


class Base(DeclarativeBase):
    pass


class ApiKeyRecordModel(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_user_id: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    key_prefix: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    key_hash_sha256: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(16), default="active", index=True)
    rate_limit_per_second: Mapped[int] = mapped_column(Integer)
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer)
    daily_quota: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rotated_from_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True, index=True)
    rotated_to_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True, index=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ApiKeyAuditEventModel(Base):
    __tablename__ = "api_key_audit_events"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    api_key_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("api_keys.id"), index=True)
    owner_user_id: Mapped[str] = mapped_column(String(128), index=True)
    actor_user_id: Mapped[str] = mapped_column(String(128), index=True)
    event_type: Mapped[str] = mapped_column(String(24), index=True)
    event_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)


@dataclass(frozen=True)
class KeyPolicy:
    rate_limit_per_second: int
    rate_limit_per_minute: int
    daily_quota: int


@dataclass(frozen=True)
class RuntimeApiKey:
    key_id: str
    owner_user_id: str
    key_prefix: str
    key_hash_sha256: str
    policy: KeyPolicy


@dataclass(frozen=True)
class KeyMetadata:
    key_id: str
    owner_user_id: str
    name: str | None
    key_prefix: str
    masked_key: str
    status: str
    policy: KeyPolicy
    created_at: datetime
    revoked_at: datetime | None
    rotated_from_id: str | None
    rotated_to_id: str | None
    last_used_at: datetime | None


@dataclass(frozen=True)
class CreatedApiKey:
    metadata: KeyMetadata
    raw_key: str


@dataclass(frozen=True)
class RotatedApiKey:
    previous_metadata: KeyMetadata
    new_key: CreatedApiKey


class ApiKeyNotFoundError(Exception):
    pass


class ApiKeyLimitExceededError(Exception):
    pass


class ApiKeyDeleteConflictError(Exception):
    pass


class DatabaseManager:
    def __init__(self, settings: Settings) -> None:
        connect_args: dict[str, Any] = {}
        database_driver = "unknown"
        database_host = "unknown"

        if settings.database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
            database_driver = "sqlite"
            database_host = "local-file"
        elif settings.database_url.startswith("postgresql+asyncpg"):
            database_driver = "postgresql+asyncpg"
            # Supabase pooler (PgBouncer) requires disabling asyncpg statement caching.
            # Keep this targeted to pooled hosts/ports so direct Postgres keeps default behavior.
            try:
                parsed = make_url(settings.database_url)
                database_host = parsed.host or "unknown"
                if database_host.endswith(".pooler.supabase.com") or parsed.port == 6543:
                    connect_args["statement_cache_size"] = 0
            except Exception:
                connect_args["statement_cache_size"] = 0

        self._settings = settings
        self._engine: AsyncEngine = create_async_engine(
            settings.database_url,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
        logger.info(
            "Database engine initialized (driver=%s host=%s statement_cache_size=%s)",
            database_driver,
            database_host,
            connect_args.get("statement_cache_size", "default"),
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def startup(self) -> None:
        if not self._settings.database_auto_create:
            return
        async with self._engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def shutdown(self) -> None:
        await self._engine.dispose()

    def session(self) -> AsyncSession:
        return self._session_factory()


def parse_api_key_prefix(raw_api_key: str | None, *, key_format_prefix: str) -> str | None:
    if not raw_api_key:
        return None
    parts = raw_api_key.split("_", 2)
    if len(parts) != 3:
        return None
    prefix_token, prefix, secret = parts
    if prefix_token != key_format_prefix:
        return None
    if len(prefix) < 4 or len(secret) < 12:
        return None
    if not prefix.isalnum():
        return None
    return prefix.lower()


def mask_api_key(prefix: str, *, key_format_prefix: str) -> str:
    return f"{key_format_prefix}_{prefix}_********"


class ApiKeyLifecycleService:
    def __init__(self, settings: Settings, database: DatabaseManager) -> None:
        self._settings = settings
        self._database = database

    async def ensure_dev_bootstrap_key(self) -> None:
        if not self._settings.dev_bootstrap_api_key_enabled:
            return
        if self._settings.is_production_like():
            return

        raw_key = self._settings.dev_bootstrap_api_key.strip()
        prefix = parse_api_key_prefix(raw_key, key_format_prefix=self._settings.api_key_format_prefix)
        if prefix is None:
            logger.warning("DEV_BOOTSTRAP_API_KEY format is invalid; skipping bootstrap seeding.")
            return

        async with self._database.session() as session:
            existing = await self._record_by_prefix(session, prefix=prefix)
            if existing is not None:
                return

            now = datetime.now(UTC)
            record = ApiKeyRecordModel(
                id=str(uuid.uuid4()),
                owner_user_id=self._settings.dev_bootstrap_owner_id,
                name="bootstrap-dev-key",
                key_prefix=prefix,
                key_hash_sha256=self.hash_raw_key(raw_key),
                status="active",
                rate_limit_per_second=self._settings.default_key_rate_limit_per_second,
                rate_limit_per_minute=self._settings.default_key_rate_limit_per_minute,
                daily_quota=self._settings.default_key_daily_quota,
                created_at=now,
            )
            session.add(record)
            await session.flush()
            session.add(
                ApiKeyAuditEventModel(
                    api_key_id=record.id,
                    owner_user_id=record.owner_user_id,
                    actor_user_id=record.owner_user_id,
                    event_type="create",
                    event_metadata={"source": "dev_bootstrap"},
                    created_at=now,
                )
            )
            await session.commit()
            logger.info("Seeded dev bootstrap key into database.")

    async def find_active_runtime_key_by_prefix(self, *, prefix: str) -> RuntimeApiKey | None:
        async with self._database.session() as session:
            model = await self._runtime_record_by_prefix(session, prefix=prefix)
            if model is None:
                return None
            return self._to_runtime(model)

    async def find_active_runtime_key_by_id(
        self,
        *,
        key_id: str,
        owner_user_id: str,
    ) -> RuntimeApiKey | None:
        async with self._database.session() as session:
            model = await session.get(ApiKeyRecordModel, key_id)
            if model is None or model.owner_user_id != owner_user_id or model.status != "active":
                return None
            return self._to_runtime(model)

    async def list_user_keys(self, *, owner_user_id: str) -> list[KeyMetadata]:
        async with self._database.session() as session:
            statement = (
                select(ApiKeyRecordModel)
                .where(ApiKeyRecordModel.owner_user_id == owner_user_id)
                .order_by(ApiKeyRecordModel.created_at.desc())
            )
            rows = await session.execute(statement)
            return [self._to_metadata(model) for model in rows.scalars().all()]

    async def create_key(
        self,
        *,
        owner_user_id: str,
        actor_user_id: str,
        name: str | None,
        event_metadata: dict[str, Any] | None = None,
    ) -> CreatedApiKey:
        async with self._database.session() as session:
            await self._assert_total_key_capacity(session, owner_user_id=owner_user_id)
            await self._assert_active_key_capacity(session, owner_user_id=owner_user_id)
            for _ in range(6):
                prefix = self._random_token(self._settings.api_key_prefix_length)
                existing = await self._record_by_prefix(session, prefix=prefix)
                if existing is not None:
                    continue

                raw_key = self._format_raw_key(prefix=prefix, secret=self._random_token(self._settings.api_key_secret_length))
                now = datetime.now(UTC)
                model = ApiKeyRecordModel(
                    id=str(uuid.uuid4()),
                    owner_user_id=owner_user_id,
                    name=name,
                    key_prefix=prefix,
                    key_hash_sha256=self.hash_raw_key(raw_key),
                    status="active",
                    rate_limit_per_second=self._settings.default_key_rate_limit_per_second,
                    rate_limit_per_minute=self._settings.default_key_rate_limit_per_minute,
                    daily_quota=self._settings.default_key_daily_quota,
                    created_at=now,
                )
                session.add(model)
                await session.flush()
                session.add(
                    ApiKeyAuditEventModel(
                        api_key_id=model.id,
                        owner_user_id=owner_user_id,
                        actor_user_id=actor_user_id,
                        event_type="create",
                        event_metadata=event_metadata or {},
                        created_at=now,
                    )
                )
                await session.commit()
                await session.refresh(model)
                return CreatedApiKey(metadata=self._to_metadata(model), raw_key=raw_key)

        raise RuntimeError("Unable to generate a unique API key prefix.")

    async def revoke_key(
        self,
        *,
        owner_user_id: str,
        actor_user_id: str,
        key_id: str,
        event_metadata: dict[str, Any] | None = None,
    ) -> KeyMetadata:
        async with self._database.session() as session:
            model = await session.get(ApiKeyRecordModel, key_id)
            if model is None or model.owner_user_id != owner_user_id:
                raise ApiKeyNotFoundError(key_id)

            if model.status == "active":
                now = datetime.now(UTC)
                model.status = "revoked"
                model.revoked_at = now
                session.add(
                    ApiKeyAuditEventModel(
                        api_key_id=model.id,
                        owner_user_id=owner_user_id,
                        actor_user_id=actor_user_id,
                        event_type="revoke",
                        event_metadata=event_metadata or {},
                        created_at=now,
                    )
                )
                await session.commit()
                await session.refresh(model)

            return self._to_metadata(model)

    async def rotate_key(
        self,
        *,
        owner_user_id: str,
        actor_user_id: str,
        key_id: str,
        event_metadata: dict[str, Any] | None = None,
    ) -> RotatedApiKey:
        async with self._database.session() as session:
            current = await session.get(ApiKeyRecordModel, key_id)
            if current is None or current.owner_user_id != owner_user_id:
                raise ApiKeyNotFoundError(key_id)
            if current.status != "active":
                raise ValueError("Only active keys can be rotated.")
            await self._assert_total_key_capacity(session, owner_user_id=owner_user_id)
            await self._assert_active_key_capacity(
                session,
                owner_user_id=owner_user_id,
                excluding_key_id=current.id,
            )

            created = await self._create_key_inside_session(
                session,
                owner_user_id=owner_user_id,
                actor_user_id=actor_user_id,
                name=current.name,
                event_metadata={**(event_metadata or {}), "rotation": True},
            )

            now = datetime.now(UTC)
            current.status = "rotated"
            current.revoked_at = now
            current.rotated_to_id = created.metadata.key_id

            new_model = await session.get(ApiKeyRecordModel, created.metadata.key_id)
            if new_model is not None:
                new_model.rotated_from_id = current.id

            session.add(
                ApiKeyAuditEventModel(
                    api_key_id=current.id,
                    owner_user_id=owner_user_id,
                    actor_user_id=actor_user_id,
                    event_type="rotate",
                    event_metadata=event_metadata or {},
                    created_at=now,
                )
            )
            await session.commit()
            await session.refresh(current)

            return RotatedApiKey(previous_metadata=self._to_metadata(current), new_key=created)

    async def delete_revoked_key(
        self,
        *,
        owner_user_id: str,
        actor_user_id: str,
        key_id: str,
        event_metadata: dict[str, Any] | None = None,
    ) -> str:
        async with self._database.session() as session:
            model = await session.get(ApiKeyRecordModel, key_id)
            if model is None or model.owner_user_id != owner_user_id:
                raise ApiKeyNotFoundError(key_id)
            if model.status != "revoked":
                raise ApiKeyDeleteConflictError("Only revoked keys can be deleted.")

            await session.execute(
                delete(ApiKeyAuditEventModel).where(ApiKeyAuditEventModel.api_key_id == model.id)
            )
            await session.execute(delete(ApiKeyRecordModel).where(ApiKeyRecordModel.id == model.id))
            await session.commit()
            return model.id

    async def delete_all_revoked_keys(
        self,
        *,
        owner_user_id: str,
        actor_user_id: str,
        event_metadata: dict[str, Any] | None = None,
    ) -> int:
        async with self._database.session() as session:
            revoked_ids_query = select(ApiKeyRecordModel.id).where(
                ApiKeyRecordModel.owner_user_id == owner_user_id,
                ApiKeyRecordModel.status == "revoked",
            )
            rows = await session.execute(revoked_ids_query)
            key_ids = [str(key_id) for key_id in rows.scalars().all()]
            if not key_ids:
                return 0

            await session.execute(
                delete(ApiKeyAuditEventModel).where(ApiKeyAuditEventModel.api_key_id.in_(key_ids))
            )
            await session.execute(
                delete(ApiKeyRecordModel).where(
                    ApiKeyRecordModel.owner_user_id == owner_user_id,
                    ApiKeyRecordModel.status == "revoked",
                    ApiKeyRecordModel.id.in_(key_ids),
                )
            )
            await session.commit()
            return len(key_ids)

    async def mark_key_used(self, *, key_id: str) -> None:
        async with self._database.session() as session:
            model = await session.get(ApiKeyRecordModel, key_id)
            if model is None:
                return
            model.last_used_at = datetime.now(UTC)
            await session.commit()

    def hash_raw_key(self, raw_key: str) -> str:
        return hmac.new(
            self._settings.api_key_hash_secret.encode("utf-8"),
            raw_key.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    async def _create_key_inside_session(
        self,
        session: AsyncSession,
        *,
        owner_user_id: str,
        actor_user_id: str,
        name: str | None,
        event_metadata: dict[str, Any] | None = None,
    ) -> CreatedApiKey:
        for _ in range(6):
            prefix = self._random_token(self._settings.api_key_prefix_length)
            existing = await self._record_by_prefix(session, prefix=prefix)
            if existing is not None:
                continue

            raw_key = self._format_raw_key(prefix=prefix, secret=self._random_token(self._settings.api_key_secret_length))
            now = datetime.now(UTC)
            model = ApiKeyRecordModel(
                id=str(uuid.uuid4()),
                owner_user_id=owner_user_id,
                name=name,
                key_prefix=prefix,
                key_hash_sha256=self.hash_raw_key(raw_key),
                status="active",
                rate_limit_per_second=self._settings.default_key_rate_limit_per_second,
                rate_limit_per_minute=self._settings.default_key_rate_limit_per_minute,
                daily_quota=self._settings.default_key_daily_quota,
                created_at=now,
            )
            session.add(model)
            await session.flush()
            session.add(
                ApiKeyAuditEventModel(
                    api_key_id=model.id,
                    owner_user_id=owner_user_id,
                    actor_user_id=actor_user_id,
                    event_type="create",
                    event_metadata=event_metadata or {},
                    created_at=now,
                )
            )
            await session.flush()
            return CreatedApiKey(metadata=self._to_metadata(model), raw_key=raw_key)

        raise RuntimeError("Unable to generate a unique API key prefix.")

    async def _runtime_record_by_prefix(self, session: AsyncSession, *, prefix: str) -> ApiKeyRecordModel | None:
        statement = select(ApiKeyRecordModel).where(
            ApiKeyRecordModel.key_prefix == prefix,
            ApiKeyRecordModel.status == "active",
        )
        row = await session.execute(statement)
        return row.scalar_one_or_none()

    async def _record_by_prefix(self, session: AsyncSession, *, prefix: str) -> ApiKeyRecordModel | None:
        statement = select(ApiKeyRecordModel).where(ApiKeyRecordModel.key_prefix == prefix)
        row = await session.execute(statement)
        return row.scalar_one_or_none()

    async def _assert_active_key_capacity(
        self,
        session: AsyncSession,
        *,
        owner_user_id: str,
        excluding_key_id: str | None = None,
    ) -> None:
        statement = select(func.count(ApiKeyRecordModel.id)).where(
            ApiKeyRecordModel.owner_user_id == owner_user_id,
            ApiKeyRecordModel.status == "active",
        )
        if excluding_key_id:
            statement = statement.where(ApiKeyRecordModel.id != excluding_key_id)

        row = await session.execute(statement)
        active_key_count = int(row.scalar_one())
        if active_key_count >= self._settings.max_active_api_keys_per_user:
            raise ApiKeyLimitExceededError(
                f"Maximum active API keys reached ({self._settings.max_active_api_keys_per_user}). "
                "Revoke an existing key or rotate one to continue."
            )

    async def _assert_total_key_capacity(
        self,
        session: AsyncSession,
        *,
        owner_user_id: str,
    ) -> None:
        statement = select(func.count(ApiKeyRecordModel.id)).where(
            ApiKeyRecordModel.owner_user_id == owner_user_id,
        )
        row = await session.execute(statement)
        total_key_count = int(row.scalar_one())
        if total_key_count >= self._settings.max_total_api_keys_per_user:
            raise ApiKeyLimitExceededError(
                f"Maximum total API key history reached ({self._settings.max_total_api_keys_per_user}). "
                "This safeguard prevents unbounded key-history growth."
            )

    def _format_raw_key(self, *, prefix: str, secret: str) -> str:
        return f"{self._settings.api_key_format_prefix}_{prefix}_{secret}"

    @staticmethod
    def _random_token(length: int) -> str:
        return "".join(secrets.choice(_ALPHABET) for _ in range(length))

    def _to_runtime(self, model: ApiKeyRecordModel) -> RuntimeApiKey:
        return RuntimeApiKey(
            key_id=model.id,
            owner_user_id=model.owner_user_id,
            key_prefix=model.key_prefix,
            key_hash_sha256=model.key_hash_sha256,
            policy=KeyPolicy(
                rate_limit_per_second=model.rate_limit_per_second,
                rate_limit_per_minute=model.rate_limit_per_minute,
                daily_quota=model.daily_quota,
            ),
        )

    def _to_metadata(self, model: ApiKeyRecordModel) -> KeyMetadata:
        return KeyMetadata(
            key_id=model.id,
            owner_user_id=model.owner_user_id,
            name=model.name,
            key_prefix=model.key_prefix,
            masked_key=mask_api_key(model.key_prefix, key_format_prefix=self._settings.api_key_format_prefix),
            status=model.status,
            policy=KeyPolicy(
                rate_limit_per_second=model.rate_limit_per_second,
                rate_limit_per_minute=model.rate_limit_per_minute,
                daily_quota=model.daily_quota,
            ),
            created_at=model.created_at,
            revoked_at=model.revoked_at,
            rotated_from_id=model.rotated_from_id,
            rotated_to_id=model.rotated_to_id,
            last_used_at=model.last_used_at,
        )
