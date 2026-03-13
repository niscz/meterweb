import { test, expect } from '@playwright/test';

test('mobile metering capture flow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('http://localhost:8000/login');

  await page.fill('input[name="username"]', 'admin');
  await page.fill('input[name="password"]', 'admin');
  await page.click('button[type="submit"]');

  await expect(page).toHaveURL(/dashboard/);
  await page.fill('form[action="/dashboard/buildings"] input[name="name"]', 'Haus Mobile');
  await page.click('form[action="/dashboard/buildings"] button');
  await expect(page.locator('text=Haus Mobile')).toBeVisible();
});
