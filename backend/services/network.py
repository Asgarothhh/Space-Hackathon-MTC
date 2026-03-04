# backend/services/network.py
import uuid
import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.models.network import Network, IPAllocation
from backend.models.projects import Project
from backend.models.compute import VirtualMachine

logger = logging.getLogger(__name__)

def _find_networks_for_project(db: Session, project_id: uuid.UUID):
    """
    Возвращает список сетей, привязанных к проекту.
    """
    return db.query(Network).filter(Network.project_id == project_id).all()

def _is_ip_allocated(db: Session, network_id: uuid.UUID, ip_address: str) -> bool:
    return db.query(IPAllocation).filter(
        IPAllocation.network_id == network_id,
        IPAllocation.ip_address == ip_address
    ).first() is not None

def allocate_ip_for_vm(db: Session, project_id: uuid.UUID, vm_id: uuid.UUID) -> Tuple[Optional[str], Optional[str]]:
    """
    Попытаться выделить IPv4 и IPv6 для VM из сетей проекта.
    Возвращает кортеж (ipv4, ipv6) — строки или None.
    Простая стратегия: для каждой сети пробуем взять первое свободное адресное пространство,
    записываем в ip_allocations и возвращаем.
    NOTE: это упрощённая реализация; в продакшене нужна корректная работа с CIDR и пулом.
    """
    ipv4 = None
    ipv6 = None
    try:
        networks = _find_networks_for_project(db, project_id)
        for net in networks:
            # простая эвристика: если cidr содержит ':' — считаем IPv6, иначе IPv4
            cidr = (net.cidr or "").strip()
            if not cidr:
                continue
            if ":" in cidr and ipv6 is None:
                # попытка выделить IPv6: формируем псевдо-адрес на основе network id (упрощённо)
                candidate = f"fd00:{net.id.hex[:4]}::1"
                if not _is_ip_allocated(db, net.id, candidate):
                    alloc = IPAllocation(network_id=net.id, vm_id=vm_id, ip_address=candidate)
                    db.add(alloc)
                    db.flush()
                    ipv6 = candidate
            elif "." in cidr and ipv4 is None:
                # попытка выделить IPv4: формируем псевдо-адрес на основе network id (упрощённо)
                candidate = f"10.{int(net.id.hex[:2], 16) % 255}.{int(net.id.hex[2:4], 16) % 255}.10"
                if not _is_ip_allocated(db, net.id, candidate):
                    alloc = IPAllocation(network_id=net.id, vm_id=vm_id, ip_address=candidate)
                    db.add(alloc)
                    db.flush()
                    ipv4 = candidate
            if ipv4 and ipv6:
                break
        # commit не делаем здесь — вызывающий код может быть в транзакции; оставляем flush
        return ipv4, ipv6
    except Exception as e:
        logger.exception("allocate_ip_for_vm failed for project %s vm %s: %s", project_id, vm_id, e)
        # в случае ошибки возвращаем None, None
        return None, None

def release_ips_for_vm(db: Session, vm_id: uuid.UUID):
    """
    Освободить все IP, связанные с vm_id (удалить записи из ip_allocations).
    """
    try:
        db.query(IPAllocation).filter(IPAllocation.vm_id == vm_id).delete(synchronize_session=False)
        db.flush()
    except Exception:
        db.rollback()
        logger.exception("Failed to release IPs for vm %s", vm_id)
