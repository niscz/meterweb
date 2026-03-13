import { test, expect } from '@playwright/test';

test('mobile metering capture flow with photo upload and exports', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('http://localhost:8000/login');

  await page.fill('input[name="username"]', 'admin');
  await page.fill('input[name="password"]', 'admin');
  await page.click('button[type="submit"]');

  await expect(page).toHaveURL(/dashboard/);
  await page.fill('form[action="/dashboard/buildings"] input[name="name"]', 'Haus Mobile');
  await page.click('form[action="/dashboard/buildings"] button');
  await expect(page.locator('text=Haus Mobile')).toBeVisible();

  await page.fill('form[action="/dashboard/units"] input[name="name"]', 'Wohnung A');
  await page.click('form[action="/dashboard/units"] button');

  await page.fill('form[action="/dashboard/meter-points"] input[name="name"]', 'Strom EG');
  await page.click('form[action="/dashboard/meter-points"] button');

  await page.fill('form[action="/dashboard/readings"] input[name="measured_at"]', '2025-01-15T08:00');
  await page.fill('form[action="/dashboard/readings"] input[name="value"]', '1234.5');
  await page.click('form[action="/dashboard/readings"] button');

  await page.setInputFiles('form[action="/dashboard/readings/photo"] input[name="photo"]', {
    name: 'meter.jpg',
    mimeType: 'image/jpeg',
    buffer: Buffer.from('/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxAQEBUQEBAVFhUVFRUVFRUVFRUVFRUVFRUXFhUVFRUYHSggGBolGxUVITEhJSkrLi4uFx8zODMsNygtLisBCgoKDg0OGhAQGi0fHyUtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLf/AABEIAAEAAQMBEQACEQEDEQH/xAAXAAADAQAAAAAAAAAAAAAAAAAAAQID/8QAFhABAQEAAAAAAAAAAAAAAAAAAQAC/9oADAMBAAIQAxAAAAGiQH//xAAVEAEBAAAAAAAAAAAAAAAAAAABAP/aAAgBAQABBQJf/8QAFBEBAAAAAAAAAAAAAAAAAAAAEP/aAAgBAwEBPwEf/8QAFBEBAAAAAAAAAAAAAAAAAAAAEP/aAAgBAgEBPwEf/8QAFBABAAAAAAAAAAAAAAAAAAAAEP/aAAgBAQAGPwJf/8QAFBABAAAAAAAAAAAAAAAAAAAAEP/aAAgBAQABPyFf/9k=', 'base64'),
  });
  await page.fill('form[action="/dashboard/readings/photo"] input[name="measured_at"]', '2025-01-16T08:00');
  await page.click('form[action="/dashboard/readings/photo"] button');
  await expect(page.locator('text=OCR Bestätigung')).toBeVisible();

  await page.goto('http://localhost:8000/dashboard');
  const reportLink = page.locator('a:has-text("Monatsbericht")').first();
  await reportLink.click();
  await expect(page.locator('text=Monatsbericht je Objekt')).toBeVisible();

  const csvHref = await page.locator('a:has-text("CSV")').getAttribute('href');
  const xlsxHref = await page.locator('a:has-text("XLSX")').getAttribute('href');
  const pdfHref = await page.locator('a:has-text("PDF")').getAttribute('href');
  expect(csvHref).toContain('/exports/csv/');
  expect(xlsxHref).toContain('/exports/xlsx/');
  expect(pdfHref).toContain('/exports/pdf/');
});
