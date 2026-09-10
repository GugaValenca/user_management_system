import { defineConfig, devices } from "@playwright/test";

/**
 * Runs against a live backend, so it's not part of `npm test`. The API must
 * already be up on http://localhost:8000 (docker compose up, or
 * `python manage.py runserver`) before running `npm run test:e2e` - this
 * config only starts the frontend dev server for you.
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  retries: 0,
  reporter: "line",
  use: {
    baseURL: "http://localhost:3000",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npm start",
    url: "http://localhost:3000",
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
