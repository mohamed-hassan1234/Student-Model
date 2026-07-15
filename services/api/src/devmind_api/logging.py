import logging
from contextvars import ContextVar
from typing import Any

from pythonjsonlogger.json import JsonFormatter

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_var.get()
        return True


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    formatter = JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s %(correlation_id)s")
    handler.setFormatter(formatter)
    handler.addFilter(CorrelationIdFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())


def safe_log_extra(**extra: Any) -> dict[str, Any]:
    return {key: "[redacted]" if "secret" in key.lower() else value for key, value in extra.items()}
