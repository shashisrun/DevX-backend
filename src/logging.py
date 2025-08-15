import structlog
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

SENSITIVE_KEYS = {"authorization", "password", "token", "api_key", "secret"}

def scrub_processor(logger, method_name, event_dict):
    # Mask sensitive fields if present
    for k in list(event_dict.keys()):
        if any(s in k.lower() for s in SENSITIVE_KEYS):
            event_dict[k] = "[REDACTED]"
    return event_dict

def setup_logging():
    logging.basicConfig(level=logging.INFO)
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            scrub_processor,
            structlog.processors.JSONRenderer()
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

class StructlogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger = structlog.get_logger()
        logger.info("request.start", method=request.method, url=str(request.url))
        response = await call_next(request)
        logger.info("request.end", status_code=response.status_code)
        return response
