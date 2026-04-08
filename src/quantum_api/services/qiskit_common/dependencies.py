from __future__ import annotations

from typing import Any

from quantum_api.services.service_errors import ProviderUnavailableError


def ensure_dependency(
    *,
    available: bool,
    provider: str,
    import_error: str | None,
    details: dict[str, Any] | None = None,
) -> None:
    if available:
        return

    payload = {"reason": "missing_dependency"}
    if import_error:
        payload["import_error"] = import_error
    if details:
        payload.update(details)
    raise ProviderUnavailableError(provider=provider, details=payload)
