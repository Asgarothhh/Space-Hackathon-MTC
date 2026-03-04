# backend/services/auth.py
import os
from datetime import datetime, timedelta
from typing import Optional
import jwt
from sqlalchemy.orm import Session
from backend.models.auth import User
from backend.services.passwords import hash_password, verify_password

SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_EXPIRE_MIN = int(os.getenv("ACCESS_EXPIRE_MINUTES", "60"))

def create_access_token(subject: str, expires_minutes: int = ACCESS_EXPIRE_MIN) -> str:
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)

def decode_token(token: str) -> str:
    payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
    return payload.get("sub")

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def register_user(db: Session, email: str, password: str, role: str = "user") -> User:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise ValueError("User with this email already exists")
    hashed = hash_password(password)
    user = User(email=email, password_hash=hashed, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
