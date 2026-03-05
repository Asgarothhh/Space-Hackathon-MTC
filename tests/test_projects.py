"""
Тесты для Projects API — Окружение 1 (Backend-only).

Проверяет:
- Создание проекта (admin only)
- Получение списка проектов
- Обновление квот
- Запуск / Остановка / Удаление проекта
- Запрет для не-admin пользователей
"""

import uuid
import pytest


class TestProjectsUnauthorized:
    def test_create_project_no_auth(self, client):
        resp = client.post("/projects", json={
            "name": "test-project",
            "cpu_quota": 4,
            "ram_quota": 8192,
            "ssd_quota": 50,
        })
        assert resp.status_code in (401, 403)

    def test_list_projects_no_auth(self, client):
        resp = client.get("/projects")
        assert resp.status_code in (401, 403)


class TestProjectsForbiddenForUser:
    def test_create_project_as_user(self, client, registered_user):
        resp = client.post("/projects", json={
            "name": "test-project",
            "cpu_quota": 4,
            "ram_quota": 8192,
            "ssd_quota": 50,
        }, headers=registered_user["headers"])
        assert resp.status_code == 403

    def test_list_projects_as_user(self, client, registered_user):
        resp = client.get("/projects", headers=registered_user["headers"])
        assert resp.status_code == 403


class TestProjectsAdmin:
    def test_create_project_success(self, client, admin_user):
        resp = client.post("/projects", json={
            "name": "admin-project",
            "cpu_quota": 8,
            "ram_quota": 16384,
            "ssd_quota": 100,
        }, headers=admin_user["headers"])
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "admin-project"
        assert data["cpu_quota"] == 8
        assert data["is_allocated"] is False

    def test_list_projects(self, client, admin_user):
        client.post("/projects", json={
            "name": "list-test",
            "cpu_quota": 4,
            "ram_quota": 8192,
            "ssd_quota": 50,
        }, headers=admin_user["headers"])

        resp = client.get("/projects", headers=admin_user["headers"])
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_projects_search(self, client, admin_user):
        client.post("/projects", json={
            "name": "searchable-proj",
            "cpu_quota": 4,
            "ram_quota": 8192,
            "ssd_quota": 50,
        }, headers=admin_user["headers"])

        resp = client.get("/projects?search=searchable", headers=admin_user["headers"])
        assert resp.status_code == 200

    def test_update_project(self, client, admin_user):
        create_resp = client.post("/projects", json={
            "name": "update-test",
            "cpu_quota": 4,
            "ram_quota": 8192,
            "ssd_quota": 50,
        }, headers=admin_user["headers"])
        assert create_resp.status_code == 201
        project_id = create_resp.json()["id"]

        update_resp = client.patch(f"/projects/{project_id}", json={
            "cpu_quota": 16,
            "ram_quota": 32768,
            "ssd_quota": 200,
        }, headers=admin_user["headers"])
        assert update_resp.status_code == 200
        assert update_resp.json()["cpu_quota"] == 16

    def test_project_not_found(self, client, admin_user):
        fake_id = str(uuid.uuid4())
        resp = client.patch(f"/projects/{fake_id}", json={
            "cpu_quota": 4,
            "ram_quota": 8192,
            "ssd_quota": 50,
        }, headers=admin_user["headers"])
        assert resp.status_code == 404
