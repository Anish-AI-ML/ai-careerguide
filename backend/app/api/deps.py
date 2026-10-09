import os, time, uuid
from collections import defaultdict, deque
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.core.security import decode_token
from app.database.session import get_db
from ..models.models import User

_hits: dict[str, deque] = defaultdict(deque)


def rate_limiter(env_name: str, default: str):
    """In-memory sliding window per client IP. Swap for Redis when running multiple workers."""
    def dep(request: Request) -> None:
        limit = int(os.getenv(env_name, default))
        key = f"{env_name}:{request.client.host if request.client else 'unknown'}"
        now, q = time.monotonic(), _hits[key]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")
        q.append(now)
    return dep


ai_rate_limit = rate_limiter("AI_RATE_LIMIT_PER_MIN", "30")
auth_rate_limit = rate_limiter("AUTH_RATE_LIMIT_PER_MIN", "10")
_bearer = HTTPBearer(auto_error=False)


def current_user(cred: HTTPAuthorizationCredentials | None = Depends(_bearer), db: Session = Depends(get_db)) -> User:
    sub = decode_token(cred.credentials) if cred else None
    try:
        user = db.get(User, uuid.UUID(sub)) if sub else None
    except ValueError:
        user = None
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
