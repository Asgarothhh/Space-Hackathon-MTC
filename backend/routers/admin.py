from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.models.db import SessionLocal
from backend.schemas.admin import (
    AdminUserInfo,
    AdminProjectCreateRequest,
    AdminProjectResponse,
    AdminVMCreateRequest,
    AdminVMResponse,
    AdminVMInfoResponse,
    AdminServersListResponse,
    AdminProjectsListResponse,
)
from backend.services import admin as admin_service


router = APIRouter(tags=["admin"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Project admin endpoints ──────────────────────────────────────────

@router.post(
    "/project/admin/add/{user_id}",
    response_model=AdminProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def admin_add_project(
    user_id: UUID,
    payload: AdminProjectCreateRequest,
    db: Session = Depends(get_db),
):
    user = admin_service.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    project = admin_service.admin_create_project(
        db,
        owner_id=user_id,
        name=payload.name,
        cpu_quota=payload.cpu_quota,
        ram_quota=payload.ram_quota,
        ssd_quota=payload.ssd_quota,
    )
    return project


@router.post(
    "/project/admin/disable/{project_id}",
    response_model=AdminProjectResponse,
)
def admin_disable_project(project_id: UUID, db: Session = Depends(get_db)):
    project = admin_service.admin_change_project_status(
        db, project_id=project_id, new_status="disabled"
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


@router.post(
    "/project/admin/active/{project_id}",
    response_model=AdminProjectResponse,
)
def admin_activate_project(project_id: UUID, db: Session = Depends(get_db)):
    project = admin_service.admin_change_project_status(
        db, project_id=project_id, new_status="active"
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


@router.delete(
    "/project/admin/delete/{project_id}",
    response_model=AdminProjectResponse,
)
def admin_delete_project(project_id: UUID, db: Session = Depends(get_db)):
    project = admin_service.admin_delete_project(db, project_id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


@router.get(
    "/project/admin/info/{project_id}",
    response_model=AdminProjectResponse,
)
def admin_project_info(project_id: UUID, db: Session = Depends(get_db)):
    project = admin_service.admin_get_project_info(db, project_id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


@router.get(
    "/projects/admin/info/{user_id}",
    response_model=AdminProjectsListResponse,
)
def admin_projects_by_user(user_id: UUID, db: Session = Depends(get_db)):
    user = admin_service.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    projects = admin_service.admin_list_projects_by_user(db, user_id=user_id)
    return AdminProjectsListResponse(projects=projects)


@router.get(
    "/projects/admin/disabled",
    response_model=AdminProjectsListResponse,
)
def admin_disabled_projects(db: Session = Depends(get_db)):
    projects = admin_service.admin_list_disabled_projects(db)
    return AdminProjectsListResponse(projects=projects)


# ── Server (VM) admin endpoints ──────────────────────────────────────

@router.post(
    "/server/admin/add/{user_id}",
    response_model=AdminVMResponse,
    status_code=status.HTTP_201_CREATED,
)
def admin_add_server(
    user_id: UUID,
    payload: AdminVMCreateRequest,
    db: Session = Depends(get_db),
):
    try:
        vm = admin_service.admin_create_vm(
            db,
            owner_id=user_id,
            name=payload.name,
            project_id=payload.project_id,
            cpu=payload.cpu,
            ram=payload.ram,
            ssd=payload.ssd,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    return vm


@router.post(
    "/server/admin/disable/{server_id}",
    response_model=AdminVMResponse,
)
def admin_disable_server(server_id: UUID, db: Session = Depends(get_db)):
    vm = admin_service.admin_change_vm_status(
        db, server_id=server_id, new_status="DISABLED"
    )
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Server not found"
        )
    return vm


@router.post(
    "/server/admin/active/{server_id}",
    response_model=AdminVMResponse,
)
def admin_activate_server(server_id: UUID, db: Session = Depends(get_db)):
    vm = admin_service.admin_change_vm_status(
        db, server_id=server_id, new_status="RUNNING"
    )
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Server not found"
        )
    return vm


@router.delete(
    "/server/admin/delete/{server_id}",
    response_model=AdminVMResponse,
)
def admin_delete_server(server_id: UUID, db: Session = Depends(get_db)):
    vm = admin_service.admin_delete_vm(db, server_id=server_id)
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Server not found"
        )
    return vm


@router.get(
    "/server/admin/info/{server_id}",
    response_model=AdminVMInfoResponse,
)
def admin_server_info(server_id: UUID, db: Session = Depends(get_db)):
    vm = admin_service.admin_get_server_info(db, server_id=server_id)
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Server not found"
        )
    load = admin_service.get_server_load(server_id)
    base = AdminVMResponse.model_validate(vm)
    return AdminVMInfoResponse(**base.model_dump(), **load)


@router.get(
    "/servers/admin/disabled",
    response_model=AdminServersListResponse,
)
def admin_disabled_servers(db: Session = Depends(get_db)):
    servers = admin_service.admin_list_disabled_servers(db)
    return AdminServersListResponse(servers=servers)


# ── User admin endpoints ─────────────────────────────────────────────

@router.post(
    "/user/admin/disable/{user_id}",
    response_model=AdminUserInfo,
)
def admin_disable_user(user_id: UUID, db: Session = Depends(get_db)):
    user = admin_service.admin_disable_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.post(
    "/user/admin/active/{user_id}",
    response_model=AdminUserInfo,
)
def admin_activate_user(user_id: UUID, db: Session = Depends(get_db)):
    user = admin_service.admin_activate_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.delete(
    "/user/admin/delete/{user_id}",
    response_model=AdminUserInfo,
)
def admin_delete_user(user_id: UUID, db: Session = Depends(get_db)):
    user = admin_service.admin_delete_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


# ── List endpoints ───────────────────────────────────────────────────
# /servers/admin/info/{user_id} и /servers/admin/info/{project_id}
# имеют одинаковый path-паттерн (оба UUID), поэтому разделены на
# .../user/{user_id} и .../project/{project_id}

@router.get(
    "/servers/admin/info/user/{user_id}",
    response_model=AdminServersListResponse,
)
def admin_servers_by_user(user_id: UUID, db: Session = Depends(get_db)):
    user = admin_service.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    servers = admin_service.admin_list_servers_by_user(db, user_id=user_id)
    return AdminServersListResponse(servers=servers)


@router.get(
    "/servers/admin/info/project/{project_id}",
    response_model=AdminServersListResponse,
)
def admin_servers_by_project(project_id: UUID, db: Session = Depends(get_db)):
    project = admin_service.admin_get_project_info(db, project_id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    servers = admin_service.admin_list_servers_by_project(
        db, project_id=project_id
    )
    return AdminServersListResponse(servers=servers)
