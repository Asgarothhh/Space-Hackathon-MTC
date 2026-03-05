# backend/routers/user.py
import pyotp
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.routers.dependencies import get_db, get_current_user
from backend.schemas.auth import UserRegisterRequest, UserResponse
from backend.schemas.user import LoginRequest, TokenResponse
from backend.services.auth import (
    register_user,
    authenticate_user,
    create_access_token,
    create_2fa_token,
    generate_totp_secret,
    get_otpauth_uri,
    verify_totp,
    decode_token,
)
from backend.services.passwords import verify_password
from backend.models.auth import User
from backend.models.compute import VirtualMachine
from backend.models.projects import Project

router = APIRouter(prefix="/user", tags=["user"])


# --- Pydantic helpers local to router ---
class TwoFASetupResponse(BaseModel):
    secret: str
    otpauth_url: str


class TwoFAVerifyRequest(BaseModel):
    twofa_token: str
    code: str


class TwoFAConfirmRequest(BaseModel):
    secret: str
    code: str


class TwoFADisableRequest(BaseModel):
    password: str
    code: Optional[str] = None


# --- Registration / Login / Me ---


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    try:
        user = register_user(db, email=payload.email, password=payload.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return UserResponse.from_orm(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Логин: если у пользователя включена 2FA, возвращаем two_fa_required + two_fa_token.
    Иначе возвращаем полноценный access_token.
    """
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if getattr(user, "is_2fa_enabled", False):
        twofa_token = create_2fa_token(str(user.id))
        return TokenResponse(access_token=None, two_fa_required=True, two_fa_token=twofa_token)

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token, two_fa_required=False)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    """
    Возвращает профиль текущего пользователя.
    Схема UserResponse не содержит password_hash и секретов 2FA.
    """
    return UserResponse.from_orm(current_user)


# --- 2FA management ---


@router.post("/2fa/setup", response_model=TwoFASetupResponse)
def setup_2fa(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Генерируем временный секрет и otpauth URI.
    Секрет не сохраняется окончательно до подтверждения (confirm).
    Клиент должен отобразить QR по otpauth_url и попросить пользователя ввести код.
    """
    secret = generate_totp_secret()
    issuer = "MyService"
    otpauth = get_otpauth_uri(secret, current_user.email, issuer)
    return TwoFASetupResponse(secret=secret, otpauth_url=otpauth)


@router.post("/2fa/confirm")
def confirm_2fa(payload: TwoFAConfirmRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Подтверждение 2FA: проверяем код, сохраняем секрет и включаем 2FA.
    """
    if not verify_totp(payload.secret, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid 2FA code")
    current_user.totp_secret = payload.secret
    current_user.is_2fa_enabled = True
    db.add(current_user)
    db.commit()
    return {"status": "2fa_enabled"}


@router.post("/2fa/verify", response_model=TokenResponse)
def verify_2fa(payload: TwoFAVerifyRequest, db: Session = Depends(get_db)):
    """
    Проверка 2fa_token + TOTP-кода: если всё верно — выдаём полноценный access_token.
    """
    try:
        token_payload: Dict[str, Any] = decode_token(payload.twofa_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired 2fa token")

    if token_payload.get("purpose") != "2fa":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token purpose")

    user_id = token_payload.get("sub")
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    secret = getattr(user, "totp_secret", None)
    if not secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA not configured for user")

    if not verify_totp(secret, payload.code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid 2FA code")

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token, two_fa_required=False)


@router.post("/2fa/disable")
def disable_2fa(payload: TwoFADisableRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Отключение 2FA: требуем пароль и (опционально) код.
    """
    if not verify_password(payload.password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    if getattr(current_user, "is_2fa_enabled", False):
        secret = getattr(current_user, "totp_secret", None) or ""
        if not payload.code or not verify_totp(secret, payload.code):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid 2FA code")

    current_user.totp_secret = None
    current_user.is_2fa_enabled = False
    db.add(current_user)
    db.commit()
    return {"status": "2fa_disabled"}


# --- Utility / search endpoints ---


@router.get("/search_projects")
def search_projects_for_user(db: Session = Depends(get_db), q: Optional[str] = None):
    """
    Возвращаем VM, размещённые в проектах, с примерным фильтром по статусу RUNNING.
    Это упрощённый пример; в реальном приложении нужно проверять права доступа.
    """
    vms = db.query(VirtualMachine).join(Project, VirtualMachine.project_id == Project.id).filter(
        VirtualMachine.status == "RUNNING"
    ).all()

    return [
        {
            "vm_id": str(vm.id),
            "vm_name": vm.name,
            "status": vm.status,
            "cpu": vm.cpu,
            "ram": vm.ram,
            "ssd": vm.ssd,
            "ssh_link": vm.ssh_link,
            "project_id": str(vm.project_id),
            "project_name": vm.project.name,
        }
        for vm in vms
    ]
