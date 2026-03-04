# backend/services/passwords.py

import os
import logging
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Конфигурация: можно переопределить через env
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))

# Контекст passlib: bcrypt с настраиваемым rounds (cost)
pwd_context = CryptContext(
    schemes=["argon2"],
    bcrypt__rounds=BCRYPT_ROUNDS,
    deprecated="auto",
)


def hash_password(plain_password: str) -> str:
    """
    Возвращает безопасный хеш пароля (строка), готовую для сохранения в БД.
    Использует bcrypt через passlib.
    """
    if not plain_password:
        raise ValueError("Password must not be empty")
    try:
        return pwd_context.hash(plain_password)
    except Exception as e:
        logger.exception("Failed to hash password: %s", e)
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие plain_password и hashed_password.
    Возвращает True, если пароль корректен.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.exception("Password verification error: %s", e)
        return False
