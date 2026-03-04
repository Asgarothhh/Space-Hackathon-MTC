from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.models.db import SessionLocal
from backend.schemas.admin import (
    AdminUserInfo,
    AdminSoftDeleteUserResponse,
    AdminServerInfo,
    AdminServerCreate,
    AdminServerStatusChange,
    AdminServerCreatedResponse,
    AdminDisabledServerSearchResult,
)
from backend.services import admin as admin_service


router = APIRouter(prefix="", tags=["admin"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── User endpoints ──────────────────────────────────────────────────

@router.get("/search/admin/user/{user_id}", response_model=AdminUserInfo)
def search_user(user_id: UUID, db: Session = Depends(get_db)):
    user = admin_service.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/user/{user_id}/admin/info", response_model=AdminUserInfo)
def user_info(user_id: UUID, db: Session = Depends(get_db)):
    user = admin_service.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete("/delete/admin/user/{user_id}", response_model=AdminSoftDeleteUserResponse)
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    user = admin_service.soft_delete_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return AdminSoftDeleteUserResponse(id=user.id, is_active=user.is_active)


# ── Server (= Project) endpoints ───────────────────────────────────

@router.get("/servers/admin/user/{user_id}", response_model=list[AdminServerInfo])
def get_user_servers(user_id: UUID, db: Session = Depends(get_db)):
    return admin_service.get_servers_for_user(db, user_id=user_id)


@router.get("/server/admin/info/{server_id}", response_model=AdminServerInfo)
def server_info(server_id: UUID, db: Session = Depends(get_db)):
    project = admin_service.get_server_by_id(db, server_id=server_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    return project


@router.post("/disable/admin/server", response_model=AdminServerInfo)
def disable_server(payload: AdminServerStatusChange, db: Session = Depends(get_db)):
    project = admin_service.change_server_status(db, server_id=payload.server_id, new_status="disabled")
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    return project


@router.post("/activate/admin/server", response_model=AdminServerInfo)
def activate_server(payload: AdminServerStatusChange, db: Session = Depends(get_db)):
    project = admin_service.change_server_status(db, server_id=payload.server_id, new_status="active")
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    return project


@router.post("/add/admin/server", response_model=AdminServerCreatedResponse, status_code=status.HTTP_201_CREATED)
def add_server(payload: AdminServerCreate, db: Session = Depends(get_db)):
    project = admin_service.create_server(
        db,
        name=payload.name,
        owner_id=payload.owner_id,
        cpu_quota=payload.cpu_quota,
        ram_quota=payload.ram_quota,
        ssd_quota=payload.ssd_quota,
    )
    return AdminServerCreatedResponse(id=project.id, name=project.name, status=project.status)


@router.delete("/delete/admin/server/{server_id}", response_model=AdminServerInfo)
def delete_server(server_id: UUID, db: Session = Depends(get_db)):
    project = admin_service.delete_server(db, server_id=server_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    return project


@router.get("/search/admin/disable/server", response_model=list[AdminDisabledServerSearchResult])
def search_disabled_servers(db: Session = Depends(get_db)):
    return admin_service.get_disabled_servers(db)


@router.get("/search/admin/disable/server/user/{user_id}", response_model=list[AdminDisabledServerSearchResult])
def search_disabled_servers_for_user(user_id: UUID, db: Session = Depends(get_db)):
    return admin_service.get_disabled_servers_for_user(db, user_id=user_id)
