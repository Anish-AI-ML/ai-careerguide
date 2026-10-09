import os, time
import bcrypt, jwt

_DUMMY = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt()).decode()


def secret() -> str:
    s = os.getenv("JWT_SECRET", "")
    if len(s) < 16 or s == "change-me":
        raise RuntimeError("JWT_SECRET must be set to a random string of 16+ characters")
    return s


def hash_password(p: str) -> str:
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()


def verify_password(p: str, hashed: str | None) -> bool:
    # Always run a bcrypt comparison so unknown emails take the same time as wrong passwords.
    try:
        ok = bcrypt.checkpw(p.encode(), (hashed or _DUMMY).encode())
    except ValueError:
        return False
    return ok and hashed is not None


def create_token(user_id: str) -> str:
    now = int(time.time())
    hours = float(os.getenv("JWT_EXPIRE_HOURS", "12"))
    return jwt.encode({"sub": user_id, "iat": now, "exp": now + int(hours * 3600)}, secret(), algorithm="HS256")


def decode_token(token: str) -> str | None:
    try:
        return jwt.decode(token, secret(), algorithms=["HS256"]).get("sub")
    except jwt.PyJWTError:
        return None
