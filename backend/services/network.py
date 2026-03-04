# backend/services/network.py
import uuid
import logging
import ipaddress
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from backend.models.network import Network, IPAllocation

logger = logging.getLogger(__name__)

def _find_networks_for_project(db: Session, project_id: uuid.UUID) -> List[Network]:
    return db.query(Network).filter(Network.project_id == project_id).all()

def _is_ip_allocated(db: Session, network_id: uuid.UUID, ip_address: str) -> bool:
    return db.query(IPAllocation).filter(
        IPAllocation.network_id == network_id,
        IPAllocation.ip_address == ip_address
    ).first() is not None

def allocate_ip_for_vm(db: Session, project_id: uuid.UUID, vm_id: uuid.UUID) -> Tuple[Optional[str], Optional[str]]:
    """
    Попытаться выделить IPv4 и/или IPv6 для VM из сетей проекта.
    Поведение:
      - если сетей нет — создать дефолтную сеть (dev-поведение);
      - пройти по сетям, парсить CIDR через ipaddress и взять первый свободный host;
      - вставить запись в ip_allocations (db.flush() выполняется здесь), но commit оставляем вызывающему коду.
    Возвращает (ipv4, ipv6) — строки или None.
    """
    ipv4 = None
    ipv6 = None
    try:
        networks = _find_networks_for_project(db, project_id)

        # Если сетей нет — создать дефолтную сеть (dev)
        if not networks:
            default_net = Network(
                id=uuid.uuid4(),
                name="default",
                project_id=project_id,
                cidr="10.10.0.0/24"
            )
            db.add(default_net)
            db.flush()
            networks = [default_net]
            logger.info("Created default network %s for project %s", default_net.id, project_id)

        for net in networks:
            cidr = (net.cidr or "").strip()
            if not cidr:
                continue
            try:
                net_obj = ipaddress.ip_network(cidr, strict=False)
            except Exception:
                logger.exception("Invalid CIDR '%s' for network %s", cidr, net.id)
                continue

            # Ищем первый свободный host в сети
            for candidate in net_obj.hosts():
                cand_str = str(candidate)
                if _is_ip_allocated(db, net.id, cand_str):
                    continue
                alloc = IPAllocation(network_id=net.id, vm_id=vm_id, ip_address=cand_str)
                db.add(alloc)
                db.flush()
                if candidate.version == 4 and ipv4 is None:
                    ipv4 = cand_str
                elif candidate.version == 6 and ipv6 is None:
                    ipv6 = cand_str
                logger.info("Allocated IP %s (network=%s) for vm %s", cand_str, net.id, vm_id)
                break  # перешли к следующей сети или завершили
            if ipv4 and ipv6:
                break

        return ipv4, ipv6
    except Exception as e:
        logger.exception("allocate_ip_for_vm failed for project %s vm %s: %s", project_id, vm_id, e)
        return None, None

def release_ips_for_vm(db: Session, vm_id: uuid.UUID):
    """
    Удалить все записи ip_allocations для vm_id.
    """
    try:
        db.query(IPAllocation).filter(IPAllocation.vm_id == vm_id).delete(synchronize_session=False)
        db.flush()
        logger.info("Released IP allocations for vm %s", vm_id)
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        logger.exception("Failed to release IPs for vm %s", vm_id)
