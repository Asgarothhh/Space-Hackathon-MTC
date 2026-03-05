"""
Тесты для User API — Окружение 1 (Backend-only).

Проверяет:
- Регистрацию пользователя
- Логин и получение токена
- Повторную регистрацию (ошибка)
- Неверные учётные данные
"""

import pytest


class TestUserRegister:
    def test_register_success(self, client):
        resp = client.post("/user/register", json={
            "email": "new@example.com",
            "password": "strongpass",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new@example.com"
        assert data["role"] == "user"
        assert data["is_active"] is True
        assert "id" in data

    def test_register_duplicate(self, client):
        payload = {"email": "dupe@example.com", "password": "pass123"}
        resp1 = client.post("/user/register", json=payload)
        assert resp1.status_code == 201

        resp2 = client.post("/user/register", json=payload)
        assert resp2.status_code == 409

    def test_register_invalid_email(self, client):
        resp = client.post("/user/register", json={
            "email": "not-an-email",
            "password": "pass123",
        })
        assert resp.status_code == 422


class TestUserLogin:
    def test_login_success(self, registered_user, client):
        resp = client.post("/user/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, registered_user, client):
        resp = client.post("/user/login", json={
            "email": registered_user["email"],
            "password": "wrong-password",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post("/user/login", json={
            "email": "nobody@example.com",
            "password": "irrelevant",
        })
        assert resp.status_code == 401


class TestUserSearch:
    def test_search_projects_returns_list(self, client):
        resp = client.get("/user/search_projects")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
