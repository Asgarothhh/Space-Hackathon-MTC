# backend/routers/vm.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from backend.routers.dependencies import get_db, get_current_user
from backend.services.vm import create_server, delete_server, update_server, start_server, create_ssh_link_for_vm, get_vm_by_id  # get_vm_by_id можно добавить в сервис
from backend.schemas.vm import VMCreate, VMResponse, VMUpdate

router = APIRouter(prefix="/vm", tags=["vm"])

@router.post("/", response_model=VMResponse, status_code=status.HTTP_201_CREATED)
def api_create_vm(payload: VMCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    vm = create_server(db, owner_id=current_user.id, name=payload.name, cpu=payload.cpu, ram=payload.ram, ssd=payload.ssd, network_speed=payload.network_speed)
    if not vm:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create VM")
    db.refresh(vm)
    return vm

@router.get("/{server_id}", response_model=VMResponse)
def api_get_vm(server_id: UUID, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    vm = get_vm_by_id(db, owner_id=current_user.id, server_id=server_id)
    if not vm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VM not found")
    return vm

@router.post("/{server_id}/ssh", status_code=status.HTTP_202_ACCEPTED)
def api_create_ssh(server_id: UUID, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    job = create_ssh_link_for_vm(db, owner_id=current_user.id, server_id=server_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VM not found or access denied")
    return {"job_id": str(job.id), "message": "SSH creation enqueued"}

@router.patch("/{server_id}", response_model=VMResponse)
def api_update_vm(server_id: UUID, payload: VMUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    vm = update_server(db, owner_id=current_user.id, server_id=server_id, cpu=payload.cpu, ram=payload.ram, ssd=payload.ssd, network_speed=payload.network_speed)
    if not vm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VM not found or access denied")
    return vm

@router.post("/{server_id}/start", response_model=VMResponse)
def api_start_vm(server_id: UUID, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    vm = start_server(db, owner_id=current_user.id, server_id=server_id)
    if not vm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VM not found or access denied")
    return vm

@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_vm(server_id: UUID, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    ok = delete_server(db, owner_id=current_user.id, server_id=server_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VM not found or access denied")
    return None
