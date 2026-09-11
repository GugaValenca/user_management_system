import { test, expect } from "@playwright/test";

/**
 * Covers the app's most critical path end to end against a live backend:
 * register -> land on the dashboard -> log out -> log back in with the
 * same credentials -> profile shows the account we created.
 */
test("register, logout, and login again with the same account", async ({ page }) => {
  const unique = Date.now();
  const email = `e2e.${unique}@example.com`;
  const username = `e2euser${unique}`;
  const password = "E2ePass123!";

  await page.goto("/register");

  await page.getByLabel(/first name/i).fill("E2E");
  await page.getByLabel(/last name/i).fill("Tester");
  await page.getByLabel(/^username$/i).fill(username);
  await page.getByLabel(/^email$/i).fill(email);
  await page.getByLabel(/^password$/i).fill(password);
  await page.getByLabel(/^confirm password$/i).fill(password);
  await page.getByRole("button", { name: /create account/i }).click();

  await expect(page.getByRole("heading", { name: /dashboard/i })).toBeVisible();

  await page.getByRole("button", { name: /e2e tester/i }).click();
  await page.getByRole("button", { name: /logout/i }).click();

  await expect(page.getByRole("heading", { name: /login/i })).toBeVisible();

  await page.getByLabel(/email or username/i).fill(email);
  await page.getByLabel(/^password$/i).fill(password);
  await page.getByRole("button", { name: /^login$/i }).click();

  await expect(page.getByRole("heading", { name: /dashboard/i })).toBeVisible();

  await page.goto("/profile");
  await expect(page.getByLabel(/^username$/i)).toHaveValue(username);
});
