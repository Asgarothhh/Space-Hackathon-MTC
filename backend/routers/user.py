from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.db import SessionLocal
from schemas.user import (
    LoginRequest,
    TokenResponse,
    UserServerCreate,
    UserServerUpdate,
    UserServerRename,
    UserServerDisable,
    UserServerDelete,
    UserProjectsSearchResponse,
    UserServerBase,
)
from sevices import user as user_service


router = APIRouter(prefix="/user", tags=["user"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user_id() -> UUID:
    # Заглушка. В реальном проекте здесь должна быть аутентификация по JWT/сессии.
    # Сейчас просто выбрасываем 401, чтобы явно показать, что нужен реальный механизм.
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication is not implemented. Replace get_current_user_id with real auth.",
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = user_service.authenticate_user(db, email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Здесь должна генерироваться реальная JWT. Пока — упрощённый токен.
    return TokenResponse(access_token=str(user.id))


@router.post("/create_server", response_model=UserServerBase, status_code=status.HTTP_201_CREATED)
def create_server(
    payload: UserServerCreate,
    db: Session = Depends(get_db),
    # В реальном проекте сюда нужно подставлять Depends с текущим пользователем
):
    # Для простоты пока ожидаем owner_id внутри токена / контекста.
    # Здесь можно будет заменить на текущего пользователя.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Bind create_server to real authenticated user.",
    )


@router.patch("/update_server", response_model=UserServerBase)
def update_server(
    payload: UserServerUpdate,
    db: Session = Depends(get_db),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Bind update_server to real authenticated user.",
    )


@router.post("/agent")
def agent():
    # Заглушка для интеграции с агентом
    return {"detail": "Agent endpoint placeholder"}


@router.delete("/delete_server", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def delete_server(
    payload: UserServerDelete,
    db: Session = Depends(get_db),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Bind delete_server to real authenticated user.",
    )


@router.post("/disable_server", response_model=UserServerBase)
def disable_server(
    payload: UserServerDisable,
    db: Session = Depends(get_db),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Bind disable_server to real authenticated user.",
    )


@router.get("/search_projects", response_model=UserProjectsSearchResponse)
def search_projects(
    q: str | None = None,
    db: Session = Depends(get_db),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Bind search_projects to real authenticated user.",
    )


@router.post("/rename_server", response_model=UserServerBase)
def rename_server(
    payload: UserServerRename,
    db: Session = Depends(get_db),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Bind rename_server to real authenticated user.",
    )

