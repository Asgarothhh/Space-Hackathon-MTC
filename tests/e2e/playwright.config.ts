import { defineConfig } from "@playwright/test";

/**
 * Конфигурация Playwright для E2E-тестов (Окружение 3 — Full-stack).
 *
 * Запуск:
 *   npx playwright test
 *   # или через Docker:
 *   make test-e2e
 */
export default defineConfig({
  testDir: "./",
  timeout: 30_000,
  retries: 1,
  use: {
    baseURL: process.env.BASE_URL || "http://localhost:8000",
    extraHTTPHeaders: {
      Accept: "application/json",
    },
  },
  projects: [
    {
      name: "api",
      testMatch: /.*\.api\.spec\.ts/,
    },
    // Раскомментируйте, когда появится фронтенд:
    // {
    //   name: "ui",
    //   testMatch: /.*\.ui\.spec\.ts/,
    //   use: {
    //     baseURL: process.env.FRONTEND_URL || "http://localhost:3000",
    //   },
    // },
  ],
});
