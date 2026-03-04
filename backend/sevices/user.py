from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.auth import User
from models.compute import VirtualMachine
from models.projects import Project


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    # В реальном проекте здесь должна быть проверка хэша пароля
    user = db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
    if not user:
        return None
    # Заглушка: считаем, что пароль всегда корректный
    return user


def get_projects_for_user(db: Session, user_id: UUID, search: Optional[str] = None) -> List[Project]:
    stmt = select(Project).where(Project.owner_id == user_id)
    if search:
        stmt = stmt.where(Project.name.ilike(f"%{search}%"))
    return list(db.scalars(stmt))


def get_server_by_id(db: Session, server_id: UUID) -> Optional[VirtualMachine]:
    return db.query(VirtualMachine).filter(VirtualMachine.id == server_id).first()


def create_server(
    db: Session,
    *,
    owner_id: UUID,
    name: str,
    project_id: UUID,
    cpu: int,
    ram: int,
    ssd: int,
) -> VirtualMachine:
    # Валидация: проект должен принадлежать пользователю
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == owner_id).first()
    if not project:
        raise ValueError("Project not found or does not belong to user")

    vm = VirtualMachine(
        name=name,
        project_id=project_id,
        cpu=cpu,
        ram=ram,
        ssd=ssd,
        status="active",
    )
    db.add(vm)
    db.commit()
    db.refresh(vm)
    return vm


def update_server(
    db: Session,
    *,
    owner_id: UUID,
    server_id: UUID,
    cpu: int | None = None,
    ram: int | None = None,
    ssd: int | None = None,
) -> Optional[VirtualMachine]:
    vm = get_server_by_id(db, server_id)
    if not vm:
        return None

    # Проверяем, что сервер принадлежит проекту пользователя
    project = db.query(Project).filter(Project.id == vm.project_id, Project.owner_id == owner_id).first()
    if not project:
        return None

    if cpu is not None:
        vm.cpu = cpu
    if ram is not None:
        vm.ram = ram
    if ssd is not None:
        vm.ssd = ssd

    db.add(vm)
    db.commit()
    db.refresh(vm)
    return vm


def rename_server(
    db: Session,
    *,
    owner_id: UUID,
    server_id: UUID,
    new_name: str,
) -> Optional[VirtualMachine]:
    vm = update_server(db, owner_id=owner_id, server_id=server_id)
    if not vm:
        return None
    vm.name = new_name
    db.add(vm)
    db.commit()
    db.refresh(vm)
    return vm


def disable_server(
    db: Session,
    *,
    owner_id: UUID,
    server_id: UUID,
) -> Optional[VirtualMachine]:
    vm = get_server_by_id(db, server_id)
    if not vm:
        return None

    project = db.query(Project).filter(Project.id == vm.project_id, Project.owner_id == owner_id).first()
    if not project:
        return None

    vm.status = "disabled"
    db.add(vm)
    db.commit()
    db.refresh(vm)
    return vm


def delete_server(
    db: Session,
    *,
    owner_id: UUID,
    server_id: UUID,
) -> bool:
    vm = get_server_by_id(db, server_id)
    if not vm:
        return False

    project = db.query(Project).filter(Project.id == vm.project_id, Project.owner_id == owner_id).first()
    if not project:
        return False

    db.delete(vm)
    db.commit()
    return True

