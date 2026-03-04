from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.db import SessionLocal
from models.compute import VirtualMachine
from schemas.admin import (
    AdminUserInfo,
    AdminSoftDeleteUserResponse,
    AdminServerInfo,
    AdminServerCreate,
    AdminServerStatusChange,
    AdminServerCreatedResponse,
    AdminDisabledServerSearchResult,
)
from sevices import admin as admin_service


router = APIRouter(prefix="/admin", tags=["admin"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/search/user/{user_id}", response_model=AdminUserInfo)
def search_user(user_id: UUID, db: Session = Depends(get_db)):
    user = admin_service.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/servers/user/{user_id}", response_model=list[AdminServerInfo])
def get_user_servers(user_id: UUID, db: Session = Depends(get_db)):
    servers: list[VirtualMachine] = admin_service.get_servers_for_user(db, user_id=user_id)
    return servers


@router.post("/disable_server", response_model=AdminServerInfo)
def disable_server(payload: AdminServerStatusChange, db: Session = Depends(get_db)):
    vm = admin_service.change_server_status(db, server_id=payload.server_id, new_status="disabled")
    if not vm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    return vm


@router.post("/activate_server", response_model=AdminServerInfo)
def activate_server(payload: AdminServerStatusChange, db: Session = Depends(get_db)):
    vm = admin_service.change_server_status(db, server_id=payload.server_id, new_status="active")
    if not vm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    return vm


@router.post("/add_server", response_model=AdminServerCreatedResponse, status_code=status.HTTP_201_CREATED)
def add_server(payload: AdminServerCreate, db: Session = Depends(get_db)):
    vm = admin_service.create_server(
        db,
        name=payload.name,
        project_id=payload.project_id,
        cpu=payload.cpu,
        ram=payload.ram,
        ssd=payload.ssd,
    )
    return AdminServerCreatedResponse(id=vm.id, name=vm.name, status=vm.status)


@router.get("/search_disable_server", response_model=list[AdminDisabledServerSearchResult])
def search_disabled_servers(db: Session = Depends(get_db)):
    disabled_servers = admin_service.get_disabled_servers(db)
    return disabled_servers


@router.delete("/delete_user/{user_id}", response_model=AdminSoftDeleteUserResponse)
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    user = admin_service.soft_delete_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return AdminSoftDeleteUserResponse(id=user.id, is_active=user.is_active)


@router.get("/user/info/{user_id}", response_model=AdminUserInfo)
def user_info(user_id: UUID, db: Session = Depends(get_db)):
    user = admin_service.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/server_info/{server_id}", response_model=AdminServerInfo)
def server_info(server_id: UUID, db: Session = Depends(get_db)):
    vm = admin_service.get_server_by_id(db, server_id=server_id)
    if not vm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    return vm

