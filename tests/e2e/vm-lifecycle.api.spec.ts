import { test, expect } from "@playwright/test";

/**
 * E2E-тест: полный жизненный цикл VM.
 *
 * Сценарий:
 *   1. Зарегистрировать пользователя
 *   2. Получить токен
 *   3. Создать VM
 *   4. Запустить VM
 *   5. Остановить VM
 *   6. Удалить VM
 */

let token: string;
let vmId: string;

test.describe.serial("VM lifecycle", () => {
  const email = `e2e-${Date.now()}@test.com`;
  const password = "e2e-test-password";

  test("register user", async ({ request }) => {
    const resp = await request.post("/user/register", {
      data: { email, password },
    });
    expect(resp.status()).toBe(201);
    const body = await resp.json();
    expect(body.email).toBe(email);
  });

  test("login", async ({ request }) => {
    const resp = await request.post("/user/login", {
      data: { email, password },
    });
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    token = body.access_token;
    expect(token).toBeTruthy();
  });

  test("create VM", async ({ request }) => {
    const resp = await request.post("/vm/", {
      headers: { Authorization: `Bearer ${token}` },
      data: { name: "e2e-vm", cpu: 1, ram: 1024, ssd: 10 },
    });
    expect(resp.status()).toBe(201);
    const body = await resp.json();
    vmId = body.id;
    expect(body.name).toBe("e2e-vm");
    expect(body.cpu).toBe(1);
  });

  test("get VM", async ({ request }) => {
    const resp = await request.get(`/vm/${vmId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body.id).toBe(vmId);
  });

  test("start VM", async ({ request }) => {
    const resp = await request.post(`/vm/${vmId}/start`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(resp.status()).toBe(200);
  });

  test("stop VM", async ({ request }) => {
    const resp = await request.post(`/vm/${vmId}/stop`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(resp.status()).toBe(200);
  });

  test("delete VM", async ({ request }) => {
    const resp = await request.delete(`/vm/${vmId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(resp.status()).toBe(204);
  });

  test("get deleted VM returns 404", async ({ request }) => {
    const resp = await request.get(`/vm/${vmId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(resp.status()).toBe(404);
  });
});
