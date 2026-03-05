# backend/services/auth.py
import os
from datetime import datetime, timedelta
from typing import Optional
import jwt
from sqlalchemy.orm import Session
from backend.models.auth import User
from backend.services.passwords import hash_password, verify_password
import pyotp
import base64
from typing import Tuple
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pyotp
SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_EXPIRE_MIN = int(os.getenv("ACCESS_EXPIRE_MINUTES", "60"))
TWO_FA_EXPIRE_MIN = int(os.getenv("TWO_FA_EXPIRE_MINUTES", "5"))
ISSUER_NAME = os.getenv("TWO_FA_ISSUER", "MyService")
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



def create_access_token(subject: str, expires_minutes: int = ACCESS_EXPIRE_MIN, purpose: Optional[str] = None) -> str:
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    payload: Dict[str, Any] = {"sub": str(subject), "exp": expire}
    if purpose:
        payload["purpose"] = purpose
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, SECRET, algorithms=[ALGORITHM])

def create_2fa_token(user_id: str) -> str:
    return create_access_token(subject=user_id, expires_minutes=TWO_FA_EXPIRE_MIN, purpose="2fa")

def generate_totp_secret() -> str:
    return pyotp.random_base32()

def get_otpauth_uri(secret: str, user_email: str, issuer: str = ISSUER_NAME) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=user_email, issuer_name=issuer)

def verify_totp(secret: str, code: str) -> bool:
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
    except Exception:
        return False

