from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from quantum_api.key_management import Base, DatabaseManager

TERMINAL_JOB_STATUSES = {"succeeded", "failed", "cancelled"}


class QuantumExecutionJobModel(Base):
    __tablename__ = "quantum_execution_jobs"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_user_id: Mapped[str] = mapped_column(String(128), index=True)
    api_key_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("api_keys.id"), index=True)
    provider: Mapped[str] = mapped_column(String(32), index=True)
    backend_name: Mapped[str] = mapped_column(String(128))
    ibm_profile_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    credential_instance: Mapped[str] = mapped_column(Text)
    credential_channel: Mapped[str] = mapped_column(String(64))
    credential_masked_token: Mapped[str] = mapped_column(String(64))
    credential_token_ciphertext: Mapped[str] = mapped_column(Text)
    remote_job_id: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(16), index=True)
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    result_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


@dataclass(frozen=True)
class ExecutionJobRecord:
    job_id: str
    owner_user_id: str
    api_key_id: str
    provider: str
    backend_name: str
    ibm_profile_name: str | None
    credential_instance: str
    credential_channel: str
    credential_masked_token: str
    credential_token_ciphertext: str
    remote_job_id: str
    status: str
    request_payload: dict[str, Any]
    result_payload: dict[str, Any] | None
    error_payload: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class QuantumExecutionJobNotFoundError(Exception):
    def __init__(self, job_id: str) -> None:
        super().__init__(job_id)
        self.job_id = job_id


class QuantumExecutionJobService:
    def __init__(self, database: DatabaseManager) -> None:
        self._database = database

    async def create_job(
        self,
        *,
        owner_user_id: str,
        api_key_id: str,
        provider: str,
        backend_name: str,
        ibm_profile_name: str | None,
        credential_instance: str,
        credential_channel: str,
        credential_masked_token: str,
        credential_token_ciphertext: str,
        remote_job_id: str,
        status: str,
        request_payload: dict[str, Any],
    ) -> ExecutionJobRecord:
        async with self._database.session() as session:
            now = datetime.now(UTC)
            model = QuantumExecutionJobModel(
                id=str(uuid.uuid4()),
                owner_user_id=owner_user_id,
                api_key_id=api_key_id,
                provider=provider,
                backend_name=backend_name,
                ibm_profile_name=ibm_profile_name,
                credential_instance=credential_instance,
                credential_channel=credential_channel,
                credential_masked_token=credential_masked_token,
                credential_token_ciphertext=credential_token_ciphertext,
                remote_job_id=remote_job_id,
                status=status,
                request_payload=request_payload,
                result_payload=None,
                error_payload=None,
                created_at=now,
                updated_at=now,
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._to_record(model)

    async def get_job(self, *, owner_user_id: str, job_id: str) -> ExecutionJobRecord:
        async with self._database.session() as session:
            model = await session.get(QuantumExecutionJobModel, job_id)
            if model is None or model.owner_user_id != owner_user_id:
                raise QuantumExecutionJobNotFoundError(job_id)
            return self._to_record(model)

    async def update_job(
        self,
        *,
        owner_user_id: str,
        job_id: str,
        status: str,
        result_payload: dict[str, Any] | None = None,
        error_payload: dict[str, Any] | None = None,
    ) -> ExecutionJobRecord:
        async with self._database.session() as session:
            model = await session.get(QuantumExecutionJobModel, job_id)
            if model is None or model.owner_user_id != owner_user_id:
                raise QuantumExecutionJobNotFoundError(job_id)

            model.status = status
            model.result_payload = result_payload
            model.error_payload = error_payload
            model.updated_at = datetime.now(UTC)
            if status in TERMINAL_JOB_STATUSES:
                model.completed_at = model.updated_at
            await session.commit()
            await session.refresh(model)
            return self._to_record(model)

    @staticmethod
    def _to_record(model: QuantumExecutionJobModel) -> ExecutionJobRecord:
        return ExecutionJobRecord(
            job_id=model.id,
            owner_user_id=model.owner_user_id,
            api_key_id=model.api_key_id,
            provider=model.provider,
            backend_name=model.backend_name,
            ibm_profile_name=model.ibm_profile_name,
            credential_instance=model.credential_instance,
            credential_channel=model.credential_channel,
            credential_masked_token=model.credential_masked_token,
            credential_token_ciphertext=model.credential_token_ciphertext,
            remote_job_id=model.remote_job_id,
            status=model.status,
            request_payload=model.request_payload,
            result_payload=model.result_payload,
            error_payload=model.error_payload,
            created_at=model.created_at,
            updated_at=model.updated_at,
            completed_at=model.completed_at,
        )
