from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.models.compute import VirtualMachine
from backend.models.projects import Project
from backend.routers.dependencies import get_db, get_current_user
from backend.schemas.auth import UserRegisterRequest, UserResponse
from backend.schemas.user import LoginRequest, TokenResponse, UserProjectsSearchResponse
from backend.services.auth import register_user, authenticate_user, create_access_token
from backend.services.user import get_projects_for_user
from backend.routers.dependencies import get_current_user   
from backend.models.auth import User

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
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token, role=user.role)

@router.get("/search_projects")
def search_projects_for_user(db: Session = Depends(get_db), q: Optional[str] = None):
    # возвращаем VM, которые размещены в проектах (фильтры по доступности/статусу)
    vms = db.query(VirtualMachine).join(Project, VirtualMachine.project_id == Project.id).filter(
        VirtualMachine.status == 'RUNNING'  # пример фильтра
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

@router.get("/admin/list")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")
    users = db.query(User).all()
    return [UserResponse.from_orm(u) for u in users]