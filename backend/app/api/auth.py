from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.deps import auth_rate_limit, current_user
from app.core.security import create_token, hash_password, verify_password
from app.database.session import get_db
from ..models.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _resp(u: User) -> dict:
    return {"access_token": create_token(str(u.id)), "token_type": "bearer", "user": {"name": u.full_name, "email": u.email}}


@router.post("/register", response_model=TokenResponse, status_code=201, dependencies=[Depends(auth_rate_limit)])
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == req.email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(email=req.email, full_name=req.full_name, password_hash=hash_password(req.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    return _resp(user)


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(auth_rate_limit)])
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == req.email))
    if not verify_password(req.password, user.password_hash if user else None):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return _resp(user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return {"name": user.full_name, "email": user.email}
