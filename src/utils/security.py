import base64
import os
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, PlainTextResponse


def _basic_auth_enabled() -> bool:
    return os.getenv("BASIC_AUTH_ENABLED", "false").lower() in {"1", "true", "yes"}


class BasicAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not _basic_auth_enabled():
            return await call_next(request)
        if request.url.path.startswith("/health") or request.url.path.startswith("/ws"):
            return await call_next(request)
        auth = request.headers.get("authorization")
        if not auth or not auth.lower().startswith("basic "):
            return PlainTextResponse("Unauthorized", status_code=401, headers={"WWW-Authenticate": "Basic"})
        try:
            userpass = base64.b64decode(auth.split(" ", 1)[1]).decode("utf-8")
            user, pwd = userpass.split(":", 1)
        except Exception:  # pragma: no cover - malformed header
            return PlainTextResponse("Unauthorized", status_code=401, headers={"WWW-Authenticate": "Basic"})
        exp_user = os.getenv("BASIC_AUTH_USER", "")
        exp_pass = os.getenv("BASIC_AUTH_PASS", "")
        if user != exp_user or pwd != exp_pass:
            return PlainTextResponse("Unauthorized", status_code=401, headers={"WWW-Authenticate": "Basic"})
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        self.cache: Dict[str, Deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        # Skip health and websockets
        if request.url.path.startswith("/health") or request.url.path.startswith("/ws"):
            return await call_next(request)
        now = time.time()
        ip = request.client.host if request.client else "anon"
        q = self.cache[ip]
        # prune old
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.max_requests:
            return PlainTextResponse("Too Many Requests", status_code=429)
        q.append(now)
        return await call_next(request)

