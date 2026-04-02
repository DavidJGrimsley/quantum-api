from __future__ import annotations

import base64
import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import Boolean, DateTime, String, Text, UniqueConstraint, Uuid, func, select
from sqlalchemy.orm import Mapped, mapped_column

from quantum_api.config import Settings
from quantum_api.key_management import Base, DatabaseManager


class IBMProfileRecordModel(Base):
    __tablename__ = "ibm_credential_profiles"
    __table_args__ = (UniqueConstraint("owner_user_id", "profile_name", name="uq_ibm_profiles_owner_name"),)

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_user_id: Mapped[str] = mapped_column(String(128), index=True)
    profile_name: Mapped[str] = mapped_column(String(128))
    token_ciphertext: Mapped[str] = mapped_column(Text)
    masked_token: Mapped[str] = mapped_column(String(64))
    instance: Mapped[str] = mapped_column(Text)
    channel: Mapped[str] = mapped_column(String(64))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    verification_status: Mapped[str] = mapped_column(String(16), default="unverified")
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


@dataclass(frozen=True)
class IBMProfileMetadata:
    profile_id: str
    owner_user_id: str
    profile_name: str
    instance: str
    channel: str
    masked_token: str
    is_default: bool
    verification_status: str
    last_verified_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ResolvedIbmCredentials:
    owner_user_id: str | None
    profile_id: str | None
    profile_name: str | None
    instance: str
    channel: str
    masked_token: str
    token: str
    token_ciphertext: str
    source: str


class IBMProfileNotFoundError(Exception):
    def __init__(self, identifier: str) -> None:
        super().__init__(identifier)
        self.identifier = identifier


class IBMDefaultProfileMissingError(Exception):
    pass


class IBMProfileConflictError(Exception):
    pass


class IBMProfileEncryptionUnavailableError(Exception):
    pass


class _ProfileCipher:
    def __init__(self, secret: str) -> None:
        digest = hashlib.sha256(secret.encode("utf-8")).digest()
        key = base64.urlsafe_b64encode(digest)
        self._fernet = Fernet(key)

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str) -> str:
        return self._fernet.decrypt(value.encode("utf-8")).decode("utf-8")


def mask_ibm_token(raw_token: str) -> str:
    stripped = raw_token.strip()
    if not stripped:
        return "********"
    if len(stripped) <= 8:
        visible = stripped[-2:]
        return f"****{visible}"
    return f"{stripped[:4]}...{stripped[-4:]}"


class IbmCredentialProfileService:
    def __init__(self, settings: Settings, database: DatabaseManager) -> None:
        self._settings = settings
        self._database = database

    async def list_profiles(self, *, owner_user_id: str) -> list[IBMProfileMetadata]:
        async with self._database.session() as session:
            statement = (
                select(IBMProfileRecordModel)
                .where(IBMProfileRecordModel.owner_user_id == owner_user_id)
                .order_by(IBMProfileRecordModel.is_default.desc(), IBMProfileRecordModel.created_at.desc())
            )
            rows = await session.execute(statement)
            return [self._to_metadata(model) for model in rows.scalars().all()]

    async def create_profile(
        self,
        *,
        owner_user_id: str,
        profile_name: str,
        token: str,
        instance: str,
        channel: str,
        is_default: bool,
    ) -> IBMProfileMetadata:
        cipher = self._cipher()
        async with self._database.session() as session:
            existing = await self._profile_by_name(session, owner_user_id=owner_user_id, profile_name=profile_name)
            if existing is not None:
                raise IBMProfileConflictError(f"IBM profile '{profile_name}' already exists.")

            current_default = await self._default_profile(session, owner_user_id=owner_user_id)
            should_default = is_default or current_default is None
            if should_default:
                await self._clear_default_profile(session, owner_user_id=owner_user_id)

            now = datetime.now(UTC)
            model = IBMProfileRecordModel(
                id=str(uuid.uuid4()),
                owner_user_id=owner_user_id,
                profile_name=profile_name,
                token_ciphertext=cipher.encrypt(token.strip()),
                masked_token=mask_ibm_token(token),
                instance=instance.strip(),
                channel=channel.strip(),
                is_default=should_default,
                verification_status="unverified",
                last_verified_at=None,
                created_at=now,
                updated_at=now,
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._to_metadata(model)

    async def update_profile(
        self,
        *,
        owner_user_id: str,
        profile_id: str,
        profile_name: str | None = None,
        token: str | None = None,
        instance: str | None = None,
        channel: str | None = None,
        is_default: bool | None = None,
    ) -> IBMProfileMetadata:
        cipher = self._cipher() if token is not None else None
        async with self._database.session() as session:
            model = await self._owned_profile_by_id(session, owner_user_id=owner_user_id, profile_id=profile_id)
            if profile_name is not None and profile_name != model.profile_name:
                existing = await self._profile_by_name(session, owner_user_id=owner_user_id, profile_name=profile_name)
                if existing is not None and existing.id != model.id:
                    raise IBMProfileConflictError(f"IBM profile '{profile_name}' already exists.")
                model.profile_name = profile_name

            credentials_changed = False
            if token is not None:
                assert cipher is not None
                model.token_ciphertext = cipher.encrypt(token.strip())
                model.masked_token = mask_ibm_token(token)
                credentials_changed = True
            if instance is not None:
                model.instance = instance.strip()
                credentials_changed = True
            if channel is not None:
                model.channel = channel.strip()
                credentials_changed = True

            if credentials_changed:
                model.verification_status = "unverified"
                model.last_verified_at = None

            if is_default is True:
                await self._clear_default_profile(session, owner_user_id=owner_user_id)
                model.is_default = True
            elif is_default is False:
                model.is_default = False

            model.updated_at = datetime.now(UTC)
            await session.commit()
            await session.refresh(model)
            return self._to_metadata(model)

    async def delete_profile(self, *, owner_user_id: str, profile_id: str) -> str:
        async with self._database.session() as session:
            model = await self._owned_profile_by_id(session, owner_user_id=owner_user_id, profile_id=profile_id)
            await session.delete(model)
            await session.commit()
            return model.id

    async def resolve_runtime_credentials(
        self,
        *,
        owner_user_id: str,
        profile_name: str | None,
    ) -> ResolvedIbmCredentials:
        async with self._database.session() as session:
            if profile_name is not None:
                model = await self._profile_by_name(session, owner_user_id=owner_user_id, profile_name=profile_name)
                if model is None:
                    raise IBMProfileNotFoundError(profile_name)
            else:
                model = await self._default_profile(session, owner_user_id=owner_user_id)
                if model is None:
                    raise IBMDefaultProfileMissingError()

            cipher = self._cipher()
            return ResolvedIbmCredentials(
                owner_user_id=model.owner_user_id,
                profile_id=model.id,
                profile_name=model.profile_name,
                instance=model.instance,
                channel=model.channel,
                masked_token=model.masked_token,
                token=self._decrypt(cipher, model.token_ciphertext),
                token_ciphertext=model.token_ciphertext,
                source="user_profile",
            )

    async def get_profile_credentials_by_id(
        self,
        *,
        owner_user_id: str,
        profile_id: str,
    ) -> ResolvedIbmCredentials:
        async with self._database.session() as session:
            model = await self._owned_profile_by_id(session, owner_user_id=owner_user_id, profile_id=profile_id)
            cipher = self._cipher()
            return ResolvedIbmCredentials(
                owner_user_id=model.owner_user_id,
                profile_id=model.id,
                profile_name=model.profile_name,
                instance=model.instance,
                channel=model.channel,
                masked_token=model.masked_token,
                token=self._decrypt(cipher, model.token_ciphertext),
                token_ciphertext=model.token_ciphertext,
                source="user_profile",
            )

    async def set_verification_status(
        self,
        *,
        owner_user_id: str,
        profile_id: str,
        status: str,
        verified_at: datetime | None,
    ) -> IBMProfileMetadata:
        async with self._database.session() as session:
            model = await self._owned_profile_by_id(session, owner_user_id=owner_user_id, profile_id=profile_id)
            model.verification_status = status
            model.last_verified_at = verified_at
            model.updated_at = datetime.now(UTC)
            await session.commit()
            await session.refresh(model)
            return self._to_metadata(model)

    def encrypt_token(self, raw_token: str) -> str:
        return self._cipher().encrypt(raw_token.strip())

    def decrypt_token(self, ciphertext: str) -> str:
        return self._decrypt(self._cipher(), ciphertext)

    async def _owned_profile_by_id(self, session, *, owner_user_id: str, profile_id: str) -> IBMProfileRecordModel:
        model = await session.get(IBMProfileRecordModel, profile_id)
        if model is None or model.owner_user_id != owner_user_id:
            raise IBMProfileNotFoundError(profile_id)
        return model

    async def _profile_by_name(
        self,
        session,
        *,
        owner_user_id: str,
        profile_name: str,
    ) -> IBMProfileRecordModel | None:
        statement = select(IBMProfileRecordModel).where(
            IBMProfileRecordModel.owner_user_id == owner_user_id,
            IBMProfileRecordModel.profile_name == profile_name,
        )
        row = await session.execute(statement)
        return row.scalar_one_or_none()

    async def _default_profile(self, session, *, owner_user_id: str) -> IBMProfileRecordModel | None:
        statement = select(IBMProfileRecordModel).where(
            IBMProfileRecordModel.owner_user_id == owner_user_id,
            IBMProfileRecordModel.is_default.is_(True),
        )
        row = await session.execute(statement)
        return row.scalar_one_or_none()

    async def _clear_default_profile(self, session, *, owner_user_id: str) -> None:
        statement = select(IBMProfileRecordModel).where(
            IBMProfileRecordModel.owner_user_id == owner_user_id,
            IBMProfileRecordModel.is_default.is_(True),
        )
        rows = await session.execute(statement)
        for model in rows.scalars().all():
            model.is_default = False
            model.updated_at = datetime.now(UTC)

    def _cipher(self) -> _ProfileCipher:
        secret = self._settings.ibm_credential_encryption_key.strip()
        if not secret:
            raise IBMProfileEncryptionUnavailableError(
                "IBM_CREDENTIAL_ENCRYPTION_KEY must be set to use stored IBM profiles."
            )
        return _ProfileCipher(secret)

    @staticmethod
    def _decrypt(cipher: _ProfileCipher, ciphertext: str) -> str:
        try:
            return cipher.decrypt(ciphertext)
        except InvalidToken as exc:
            raise IBMProfileEncryptionUnavailableError("Unable to decrypt stored IBM credentials.") from exc

    @staticmethod
    def _to_metadata(model: IBMProfileRecordModel) -> IBMProfileMetadata:
        return IBMProfileMetadata(
            profile_id=model.id,
            owner_user_id=model.owner_user_id,
            profile_name=model.profile_name,
            instance=model.instance,
            channel=model.channel,
            masked_token=model.masked_token,
            is_default=bool(model.is_default),
            verification_status=model.verification_status,
            last_verified_at=model.last_verified_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
