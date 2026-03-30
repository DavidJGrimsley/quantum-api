from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from quantum_api.config import Settings, get_settings
from quantum_api.request_context import get_api_key_id, get_request_id


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        if not hasattr(record, "api_key_id"):
            record.api_key_id = get_api_key_id()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if getattr(record, "request_id", None):
            payload["request_id"] = record.request_id

        for field in ("event", "method", "path", "status_code", "duration_ms", "client_ip", "api_key_id"):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


def setup_logging(settings: Settings | None = None) -> None:
    runtime_settings = settings or get_settings()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.addFilter(RequestContextFilter())

    if runtime_settings.app_env_normalized == "development":
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(name)s] [%(request_id)s] %(message)s")
        )
    else:
        handler.setFormatter(JsonFormatter())

    root_logger.addHandler(handler)
