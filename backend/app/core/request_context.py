"""Per-request context propagated through async execution without threading.

`request_id` is generated per request; `correlation_id` is optional and carried
from the client when a safe value is supplied. Structured loggers read these via
a logging.Filter so every record emitted inside a request is attributed to it.
"""

import contextvars
import uuid

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")
correlation_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)


def new_request_id() -> str:
    return uuid.uuid4().hex


def set_request_id(request_id: str) -> contextvars.Token:
    return request_id_var.set(request_id)


def get_request_id() -> str:
    return request_id_var.get()


def set_correlation_id(correlation_id: str | None) -> contextvars.Token:
    return correlation_id_var.set(correlation_id)


def get_correlation_id() -> str | None:
    return correlation_id_var.get()


def reset(token: contextvars.Token) -> None:
    request_id_var.reset(token)
