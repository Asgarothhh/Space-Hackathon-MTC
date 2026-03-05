"""
Тесты для Admin API — Окружение 1 (Backend-only).

Проверяет:
- Admin CRUD для проектов
- Admin CRUD для серверов
- Admin управление пользователями
- Disabled/Active статусы
"""

import uuid
import pytest


class TestAdminProjects:
    def test_add_project_for_user(self, client, registered_user):
        resp = client.post(f"/project/admin/add/{registered_user['user_id']}", json={
            "name": "admin-assigned-project",
            "cpu_quota": 8,
            "ram_quota": 16384,
            "ssd_quota": 100,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "admin-assigned-project"
        assert "created_at" in data

    def test_add_project_user_not_found(self, client):
        fake_id = str(uuid.uuid4())
        resp = client.post(f"/project/admin/add/{fake_id}", json={
            "name": "ghost-project",
        })
        assert resp.status_code == 404

    def test_disable_activate_project(self, client, registered_user):
        create_resp = client.post(f"/project/admin/add/{registered_user['user_id']}", json={
            "name": "toggle-project",
        })
        assert create_resp.status_code == 201
        project_id = create_resp.json()["id"]

        disable_resp = client.post(f"/project/admin/disable/{project_id}")
        assert disable_resp.status_code == 200

        activate_resp = client.post(f"/project/admin/active/{project_id}")
        assert activate_resp.status_code == 200

    def test_get_project_info(self, client, registered_user):
        create_resp = client.post(f"/project/admin/add/{registered_user['user_id']}", json={
            "name": "info-project",
        })
        project_id = create_resp.json()["id"]

        info_resp = client.get(f"/project/admin/info/{project_id}")
        assert info_resp.status_code == 200
        assert info_resp.json()["name"] == "info-project"

    def test_list_projects_by_user(self, client, registered_user):
        resp = client.get(f"/projects/admin/info/{registered_user['user_id']}")
        assert resp.status_code == 200
        assert "projects" in resp.json()

    def test_list_disabled_projects(self, client):
        resp = client.get("/projects/admin/disabled")
        assert resp.status_code == 200
        assert "projects" in resp.json()

    def test_delete_project(self, client, registered_user):
        create_resp = client.post(f"/project/admin/add/{registered_user['user_id']}", json={
            "name": "delete-me-project",
        })
        project_id = create_resp.json()["id"]

        del_resp = client.delete(f"/project/admin/delete/{project_id}")
        assert del_resp.status_code == 200


class TestAdminUsers:
    def test_disable_user(self, client, registered_user):
        resp = client.post(f"/user/admin/disable/{registered_user['user_id']}")
        assert resp.status_code == 200

    def test_activate_user(self, client, registered_user):
        client.post(f"/user/admin/disable/{registered_user['user_id']}")
        resp = client.post(f"/user/admin/active/{registered_user['user_id']}")
        assert resp.status_code == 200

    def test_disable_nonexistent_user(self, client):
        fake_id = str(uuid.uuid4())
        resp = client.post(f"/user/admin/disable/{fake_id}")
        assert resp.status_code == 404

    def test_delete_user(self, client, registered_user):
        resp = client.delete(f"/user/admin/delete/{registered_user['user_id']}")
        assert resp.status_code == 200


class TestAdminServers:
    def test_list_disabled_servers(self, client):
        resp = client.get("/servers/admin/disabled")
        assert resp.status_code == 200
        assert "servers" in resp.json()

    def test_server_info_not_found(self, client):
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/server/admin/info/{fake_id}")
        assert resp.status_code == 404
