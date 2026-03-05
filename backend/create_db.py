#!/usr/bin/env python3
"""
Создаёт БД с параметрами из переменных окружения (как в backend.models.db).
Запуск: python -m backend.create_db
"""
import os
import sys

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

_db_user = os.getenv("POSTGRES_USER", "postgres")
_db_password = os.getenv("POSTGRES_PASSWORD", "123789963741")
_db_host = os.getenv("POSTGRES_HOST", "localhost")
_db_port = os.getenv("POSTGRES_PORT", "5432")
_db_name = os.getenv("POSTGRES_DB", "mts")


def main():
    # Подключаемся к служебной БД postgres (она всегда есть)
    conn = psycopg2.connect(
        host=_db_host,
        port=_db_port,
        user=_db_user,
        password=_db_password or None,
        dbname="postgres",
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Проверяем, есть ли уже такая БД
    cur.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (_db_name,),
    )
    if cur.fetchone():
        print(f"База данных '{_db_name}' уже существует.")
        cur.close()
        conn.close()
        return 0

    cur.execute(f'CREATE DATABASE "{_db_name}"')
    print(f"База данных '{_db_name}' создана (host={_db_host}, port={_db_port}, user={_db_user}).")
    cur.close()
    conn.close()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except psycopg2.Error as e:
        print(f"Ошибка PostgreSQL: {e}", file=sys.stderr)
        sys.exit(1)
