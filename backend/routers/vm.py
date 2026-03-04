# backend/routers/vm.py
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from sqlalchemy.orm import Session
from typing import Optional

from backend.models.compute import VirtualMachine
from backend.routers.dependencies import get_db, get_current_user
from backend.schemas.user import (
    UserServerCreate,
    UserServerBase,
    UserServerUpdate,
    UserServerDelete,
    UserServerDisable,
    UserServerRename,
)
from backend.services.vm import (
    create_server,
    update_server,
    delete_server,
    disable_server,
    rename_server as svc_rename_server,
    start_server, create_ssh_link_for_vm,
)

router = APIRouter(prefix="/vm", tags=["vm"])


@router.post("/create", response_model=UserServerBase, status_code=status.HTTP_201_CREATED)
def create_server_endpoint(payload: UserServerCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Пользователь создаёт VM. Проект (tenant) подбирается автоматически (best-fit),
    привязывается к пользователю и ресурсы резервируются.
    В payload НЕ должно быть поля project_id.
    """
    try:
        vm = create_server(
            db,
            owner_id=current_user.id,
            name=payload.name,
            cpu=payload.cpu,
            ram=payload.ram,
            ssd=payload.ssd,
        )
    except ValueError as e:
        msg = str(e)
        if "No suitable project" in msg or "Quota" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    return UserServerBase.from_orm(vm)


@router.patch("/update", response_model=UserServerBase)
def update_server_endpoint(payload: UserServerUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    vm = update_server(db, owner_id=current_user.id, server_id=payload.server_id, cpu=payload.cpu, ram=payload.ram, ssd=payload.ssd)
    if not vm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VM not found or access denied")
    return UserServerBase.from_orm(vm)


@router.post("/rename", response_model=UserServerBase)
def rename_server_endpoint(payload: UserServerRename, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    vm = svc_rename_server(db, owner_id=current_user.id, server_id=payload.server_id, new_name=payload.new_name)
    if not vm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VM not found or access denied")
    return UserServerBase.from_orm(vm)


@router.post("/start", response_model=UserServerBase)
def start_server_endpoint(payload: UserServerDelete, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        vm = start_server(db, owner_id=current_user.id, server_id=payload.server_id)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg:
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=409, detail=msg)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")
    return UserServerBase.from_orm(vm)


@router.post("/disable", response_model=UserServerBase)
def disable_server_endpoint(payload: UserServerDisable, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    vm = disable_server(db, owner_id=current_user.id, server_id=payload.server_id)
    if not vm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VM not found or access denied")
    return UserServerBase.from_orm(vm)


@router.delete("/delete/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_server_endpoint(server_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        vm_uuid = UUID(server_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid server_id format")
    ok = delete_server(db, owner_id=current_user.id, server_id=vm_uuid)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VM not found or access denied")
    return None


@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_server_by_body(payload: dict, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    server_id = payload.get("server_id")
    if not server_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="server_id is required in body")
    try:
        vm_uuid = UUID(server_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid server_id format")
    ok = delete_server(db, owner_id=current_user.id, server_id=vm_uuid)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VM not found or access denied")
    return None


@router.post("/{server_id}/ssh", response_model=UserServerBase)
def create_vm_ssh_endpoint(server_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Пользователь запрашивает генерацию SSH для своей VM.
    Возвращает обновлённую VM (если ssh_link доступен) или 202/409 в зависимости от состояния.
    """
    try:
        vm_uuid = UUID(server_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid server_id format")

    job = create_ssh_link_for_vm(db, owner_id=current_user.id, server_id=vm_uuid)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VM not found or access denied")

    # Попытаемся вернуть обновлённую VM (если ssh_link уже записан)
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_uuid).first()
    if vm and vm.ssh_link:
        return UserServerBase.from_orm(vm)

    # Если ssh ещё не готов — вернуть 202 с текущим состоянием VM (без ssh)
    raise HTTPException(status_code=status.HTTP_202_ACCEPTED, detail=f"SSH creation enqueued (job_id={job.id})")
