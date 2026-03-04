from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.routers.dependencies import get_db, get_current_user
from backend.schemas.project import ProjectCreateRequest, ProjectResponse
from backend.services.project import create_project

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project_endpoint(payload: ProjectCreateRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        project = create_project(
            db,
            owner_id=current_user.id,
            name=payload.name,
            cpu_quota=payload.cpu_quota,
            ram_quota=payload.ram_quota,
            ssd_quota=payload.ssd_quota,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ProjectResponse.from_orm(project)
