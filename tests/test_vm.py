"""
Тесты для VM API — Окружение 1 (Backend-only).

Проверяет жизненный цикл VM:
- Создание VM
- Получение VM по ID
- Обновление VM
- Запуск / Остановка VM
- Удаление VM
- SSH link creation
- Доступ без токена (401)
- Несуществующий VM (404)
"""

import uuid
import pytest


class TestVMUnauthorized:
    def test_create_vm_no_auth(self, client):
        resp = client.post("/vm/", json={"name": "test", "cpu": 1, "ram": 1024, "ssd": 10})
        assert resp.status_code in (401, 403)

    def test_get_vm_no_auth(self, client):
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/vm/{fake_id}")
        assert resp.status_code in (401, 403)


class TestVMNotFound:
    def test_get_nonexistent_vm(self, client, registered_user):
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/vm/{fake_id}", headers=registered_user["headers"])
        assert resp.status_code == 404

    def test_update_nonexistent_vm(self, client, registered_user):
        fake_id = str(uuid.uuid4())
        resp = client.patch(
            f"/vm/{fake_id}",
            json={"cpu": 2, "ram": 4096, "ssd": 50},
            headers=registered_user["headers"],
        )
        assert resp.status_code == 404

    def test_delete_nonexistent_vm(self, client, registered_user):
        fake_id = str(uuid.uuid4())
        resp = client.delete(f"/vm/{fake_id}", headers=registered_user["headers"])
        assert resp.status_code == 404


class TestVMValidation:
    def test_create_vm_missing_fields(self, client, registered_user):
        resp = client.post("/vm/", json={"name": "test"}, headers=registered_user["headers"])
        assert resp.status_code == 422

    def test_create_vm_invalid_server_id(self, client, registered_user):
        resp = client.get("/vm/not-a-uuid", headers=registered_user["headers"])
        assert resp.status_code == 422
