from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class QuantumApiErrorPayload:
    error: str | None = None
    message: str | None = None
    details: Any = None
    request_id: str | None = None


class QuantumApiError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        body_text: str,
        headers: dict[str, str],
        payload: QuantumApiErrorPayload | None = None,
    ) -> None:
        message = payload.message if payload and payload.message else f"Quantum API request failed with status {status_code}"
        super().__init__(message)
        self.status_code = status_code
        self.body_text = body_text
        self.headers = headers
        self.code = payload.error if payload else None
        self.details = payload.details if payload else None
        self.request_id = payload.request_id if payload else None
