from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from models.auth import User
from models.compute import VirtualMachine


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def soft_delete_user(db: Session, user_id: UUID) -> User | None:
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    user.is_active = False
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_servers_for_user(db: Session, user_id: UUID) -> List[VirtualMachine]:
    # Выбираем все ВМ, принадлежащие проектам пользователя
    return (
        db.query(VirtualMachine)
        .filter(VirtualMachine.project_id.in_(
            # projects.project_service.projects.owner_id = user_id
            db.execute(
                "SELECT id FROM project_service.projects WHERE owner_id = :user_id",
                {"user_id": str(user_id)},
            ).scalars()
        ))
        .all()
    )


def get_server_by_id(db: Session, server_id: UUID) -> VirtualMachine | None:
    return db.query(VirtualMachine).filter(VirtualMachine.id == server_id).first()


def create_server(
    db: Session,
    *,
    name: str,
    project_id: UUID,
    cpu: int,
    ram: int,
    ssd: int,
    network_speed: int | None = None,
    network_ipv4: str | None = None,
    network_ipv6: str | None = None,
) -> VirtualMachine:
    vm = VirtualMachine(
        name=name,
        project_id=project_id,
        cpu=cpu,
        ram=ram,
        ssd=ssd,
        network_speed=network_speed,
        network_ipv4=network_ipv4,
        network_ipv6=network_ipv6,
        status="active",
    )
    db.add(vm)
    db.commit()
    db.refresh(vm)
    return vm


def change_server_status(
    db: Session,
    *,
    server_id: UUID,
    new_status: str,
) -> VirtualMachine | None:
    vm = get_server_by_id(db, server_id)
    if not vm:
        return None
    vm.status = new_status
    db.add(vm)
    db.commit()
    db.refresh(vm)
    return vm


def get_disabled_servers(db: Session) -> List[VirtualMachine]:
    return db.query(VirtualMachine).filter(VirtualMachine.status == "disabled").all()

