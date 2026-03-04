# backend/routers/projects.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List

from backend.routers.dependencies import get_db, get_current_user
from backend.services.project import (
    create_project,
    start_project,
    stop_project,
    delete_project,
    update_project,
    get_projects_for_admin,
)
from backend.schemas.project import ProjectCreateRequest, ProjectResponse, ProjectUpdateRequest, ProjectActionResponse

router = APIRouter(prefix="/projects", tags=["projects"])


def require_admin(user):
    if getattr(user, "role", None) != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project_endpoint(payload: ProjectCreateRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    require_admin(current_user)
    try:
        # Admin creates a template project (tenant). owner_id is left None;
        # it will be assigned later when a user requests a VM and the project is allocated.
        project = create_project(
            db,
            owner_id=None,
            name=payload.name,
            cpu_quota=payload.cpu_quota,
            ram_quota=payload.ram_quota,
            ssd_quota=payload.ssd_quota,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ProjectResponse.from_orm(project)


@router.get("", response_model=List[ProjectResponse])
def list_projects_endpoint(search: Optional[str] = Query(None, description="Filter projects by name"), db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Admin-only: list all projects. Optional query param `search` filters by project name (ILIKE).
    """
    require_admin(current_user)
    projects = get_projects_for_admin(db, search=search)
    return [ProjectResponse.from_orm(p) for p in projects]


@router.post("/{project_id}/start", status_code=status.HTTP_202_ACCEPTED)
def start_project_endpoint(project_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    require_admin(current_user)
    try:
        pid = UUID(project_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project_id format")
    job = start_project(db, owner_id=current_user.id, project_id=pid, is_admin=True)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or access denied")
    return {"job_id": str(job.id), "status": job.status}


@router.post("/{project_id}/stop", status_code=status.HTTP_202_ACCEPTED)
def stop_project_endpoint(project_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    require_admin(current_user)
    try:
        pid = UUID(project_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project_id format")
    job = stop_project(db, owner_id=current_user.id, project_id=pid, is_admin=True)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or access denied")
    return {"job_id": str(job.id), "status": job.status}


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project_endpoint(project_id: str, payload: ProjectUpdateRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    require_admin(current_user)
    try:
        pid = UUID(project_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project_id format")
    project = update_project(db, owner_id=current_user.id, project_id=pid, cpu_quota=payload.cpu_quota, ram_quota=payload.ram_quota, ssd_quota=payload.ssd_quota, is_admin=True)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or access denied")
    return ProjectResponse.from_orm(project)


@router.delete("/{project_id}", status_code=status.HTTP_202_ACCEPTED)
def delete_project_endpoint(project_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    require_admin(current_user)
    try:
        pid = UUID(project_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project_id format")
    job = delete_project(db, owner_id=current_user.id, project_id=pid, is_admin=True)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or access denied")
    return {"job_id": str(job.id), "status": job.status}
