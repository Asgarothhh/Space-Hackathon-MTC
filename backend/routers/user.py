# backend/routers/user.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.routers.dependencies import get_db, get_current_user
from backend.schemas.auth import UserRegisterRequest, UserResponse
from backend.schemas.user import (
    LoginRequest,
    TokenResponse,
    UserServerCreate,
    UserServerBase,
    UserServerUpdate,
    UserServerDelete,
    UserServerDisable,
    UserServerRename,
    UserProjectsSearchResponse,
)
from backend.services.auth import register_user, authenticate_user, create_access_token
from backend.services.user import (
    create_server,
    update_server,
    delete_server,
    disable_server,
    get_projects_for_user,
    rename_server as svc_rename_server,
)

router = APIRouter(prefix="/user", tags=["user"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    try:
        user = register_user(db, email=payload.email, password=payload.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return UserResponse.from_orm(user)

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)


import logging

logger = logging.getLogger("app.debug")

@router.post("/create_server", response_model=UserServerBase, status_code=status.HTTP_201_CREATED)
def create_server_endpoint(payload: UserServerCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    logger.info("create_server_endpoint called by user=%s project_id=%r payload=%s", current_user.id, payload.project_id, payload.dict())
    # Диагностическая проверка наличия проекта и владельца (временно)
    from backend.models.projects import Project  # локальный импорт, чтобы не ломать импорты модуля
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {payload.project_id} not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail=f"Project owner mismatch: project.owner_id={project.owner_id}, current_user.id={current_user.id}")

    try:
        vm = create_server(db, owner_id=current_user.id, name=payload.name, project_id=payload.project_id, cpu=payload.cpu, ram=payload.ram, ssd=payload.ssd)
    except ValueError as e:
        logger.info("create_server returned ValueError: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error in create_server_endpoint: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    return UserServerBase.from_orm(vm)


@router.patch("/update_server", response_model=UserServerBase)
def update_server_endpoint(payload: UserServerUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    vm = update_server(db, owner_id=current_user.id, server_id=payload.server_id, cpu=payload.cpu, ram=payload.ram, ssd=payload.ssd)
    if not vm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VM not found or access denied")
    return UserServerBase.from_orm(vm)

@router.post("/rename_server", response_model=UserServerBase)
def rename_server_endpoint(payload: UserServerRename, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    vm = svc_rename_server(db, owner_id=current_user.id, server_id=payload.server_id, new_name=payload.new_name)
    if not vm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VM not found or access denied")
    return UserServerBase.from_orm(vm)

@router.delete("/delete_server", status_code=status.HTTP_204_NO_CONTENT)
def delete_server_endpoint(payload: UserServerDelete, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    ok = delete_server(db, owner_id=current_user.id, server_id=payload.server_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VM not found or access denied")
    return None

@router.post("/disable_server", response_model=UserServerBase)
def disable_server_endpoint(payload: UserServerDisable, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    vm = disable_server(db, owner_id=current_user.id, server_id=payload.server_id)
    if not vm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VM not found or access denied")
    return UserServerBase.from_orm(vm)

@router.get("/search_projects", response_model=UserProjectsSearchResponse)
def search_projects(q: str | None = None, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    projects = get_projects_for_user(db, user_id=current_user.id, search=q)
    return UserProjectsSearchResponse(projects=[{"id": str(p.id), "name": p.name} for p in projects])
