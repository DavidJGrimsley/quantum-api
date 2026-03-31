from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import delete, func, select

from quantum_api.config import get_settings
from quantum_api.key_management import (
    ApiKeyAuditEventModel,
    ApiKeyLifecycleService,
    ApiKeyRecordModel,
    DatabaseManager,
)
from quantum_api.security import ApiKeyAuthService


@dataclass(frozen=True)
class VerificationResult:
    owner_user_id: str
    auth_create_ok: bool
    auth_old_after_rotate: bool
    auth_new_after_rotate: bool
    auth_new_after_revoke: bool
    key_statuses: list[str]
    event_counts: dict[str, int]


EXPECTED_EVENT_COUNTS = {
    "create": 2,
    "rotate": 1,
    "revoke": 1,
}


async def _cleanup_owner_rows(database: DatabaseManager, owner_user_id: str) -> None:
    async with database.session() as session:
        await session.execute(
            delete(ApiKeyAuditEventModel).where(ApiKeyAuditEventModel.owner_user_id == owner_user_id)
        )
        await session.execute(
            delete(ApiKeyRecordModel).where(ApiKeyRecordModel.owner_user_id == owner_user_id)
        )
        await session.commit()


def _verify_result(result: VerificationResult) -> list[str]:
    failures: list[str] = []

    if not result.auth_create_ok:
        failures.append("create auth check failed (new key was not accepted).")
    if result.auth_old_after_rotate:
        failures.append("rotate auth check failed (old key still accepted after rotate).")
    if not result.auth_new_after_rotate:
        failures.append("rotate auth check failed (new key not accepted after rotate).")
    if result.auth_new_after_revoke:
        failures.append("revoke auth check failed (revoked key still accepted).")

    expected_statuses = {"rotated", "revoked"}
    if set(result.key_statuses) != expected_statuses:
        failures.append(
            f"unexpected key statuses {result.key_statuses}; expected exactly {sorted(expected_statuses)}."
        )

    if result.event_counts != EXPECTED_EVENT_COUNTS:
        failures.append(
            f"unexpected audit event counts {result.event_counts}; expected {EXPECTED_EVENT_COUNTS}."
        )

    return failures


async def run_verification(*, owner_prefix: str, cleanup: bool) -> int:
    settings = get_settings()
    database = DatabaseManager(settings)
    lifecycle = ApiKeyLifecycleService(settings, database)
    auth_service = ApiKeyAuthService(settings, lifecycle)

    owner_user_id = (
        f"{owner_prefix}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
    )
    actor_user_id = owner_user_id

    try:
        await database.startup()
        await auth_service.startup_check()

        created = await lifecycle.create_key(
            owner_user_id=owner_user_id,
            actor_user_id=actor_user_id,
            name="rollback-verification",
        )
        auth_create_ok = bool(await auth_service.authenticate(created.raw_key))

        rotated = await lifecycle.rotate_key(
            owner_user_id=owner_user_id,
            actor_user_id=actor_user_id,
            key_id=created.metadata.key_id,
        )
        await auth_service.invalidate_key_prefix(rotated.previous_metadata.key_prefix)
        await auth_service.invalidate_key_prefix(rotated.new_key.metadata.key_prefix)

        auth_old_after_rotate = bool(await auth_service.authenticate(created.raw_key))
        auth_new_after_rotate = bool(await auth_service.authenticate(rotated.new_key.raw_key))

        revoked = await lifecycle.revoke_key(
            owner_user_id=owner_user_id,
            actor_user_id=actor_user_id,
            key_id=rotated.new_key.metadata.key_id,
        )
        await auth_service.invalidate_key_prefix(revoked.key_prefix)
        auth_new_after_revoke = bool(await auth_service.authenticate(rotated.new_key.raw_key))

        key_statuses = sorted(key.status for key in await lifecycle.list_user_keys(owner_user_id=owner_user_id))

        async with database.session() as session:
            rows = await session.execute(
                select(ApiKeyAuditEventModel.event_type, func.count(ApiKeyAuditEventModel.id))
                .where(ApiKeyAuditEventModel.owner_user_id == owner_user_id)
                .group_by(ApiKeyAuditEventModel.event_type)
            )
            event_counts = {str(row[0]): int(row[1]) for row in rows.all()}

        result = VerificationResult(
            owner_user_id=owner_user_id,
            auth_create_ok=auth_create_ok,
            auth_old_after_rotate=auth_old_after_rotate,
            auth_new_after_rotate=auth_new_after_rotate,
            auth_new_after_revoke=auth_new_after_revoke,
            key_statuses=key_statuses,
            event_counts=event_counts,
        )

        failures = _verify_result(result)
        if failures:
            print("Lifecycle verification: FAIL")
            print(f"Owner user id: {result.owner_user_id}")
            for failure in failures:
                print(f"- {failure}")
            return 1

        print("Lifecycle verification: PASS")
        print(f"Owner user id: {result.owner_user_id}")
        print(f"Event counts: {result.event_counts}")
        print(f"Key statuses: {result.key_statuses}")
        return 0
    finally:
        try:
            if cleanup:
                await _cleanup_owner_rows(database, owner_user_id)
        finally:
            await auth_service.close()
            await database.shutdown()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify API key lifecycle behavior (create, rotate, revoke) against the configured database/auth services."
        )
    )
    parser.add_argument(
        "--owner-prefix",
        default="phase375-verify",
        help="Prefix for temporary verification owner_user_id rows.",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete verification rows after run (recommended for normal verification).",
    )
    args = parser.parse_args()
    return asyncio.run(run_verification(owner_prefix=args.owner_prefix, cleanup=args.cleanup))


if __name__ == "__main__":
    sys.exit(main())
