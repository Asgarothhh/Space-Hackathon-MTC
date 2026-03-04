from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.routers.dependencies import get_db, get_current_user
from backend.schemas.auth import UserRegisterRequest, UserResponse
from backend.schemas.user import LoginRequest, TokenResponse, UserProjectsSearchResponse
from backend.services.auth import register_user, authenticate_user, create_access_token
from backend.services.user import get_projects_for_user

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


@router.get("/search_projects", response_model=UserProjectsSearchResponse)
def search_projects(q: str | None = None, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    projects = get_projects_for_user(db, user_id=current_user.id, search=q)
    return UserProjectsSearchResponse(projects=[{"id": str(p.id), "name": p.name} for p in projects])
