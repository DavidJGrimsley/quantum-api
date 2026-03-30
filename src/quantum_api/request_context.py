from __future__ import annotations

from contextvars import ContextVar

request_id_context: ContextVar[str | None] = ContextVar("request_id_context", default=None)
api_key_id_context: ContextVar[str | None] = ContextVar("api_key_id_context", default=None)


def get_request_id() -> str | None:
    return request_id_context.get()


def get_api_key_id() -> str | None:
    return api_key_id_context.get()
