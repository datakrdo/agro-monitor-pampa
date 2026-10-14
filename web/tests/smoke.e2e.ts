import { expect, test } from '@playwright/test';

test('la página carga, el mapa se dibuja y buscar un departamento actualiza el panel', async ({ page }) => {
	const errores: string[] = [];
	page.on('pageerror', (e) => errores.push(e.message));
	page.on('console', (m) => m.type() === 'error' && !m.text().includes('tiles.openfreemap.org') && errores.push(m.text()));

	await page.goto('/');
	await expect(page.getByRole('heading', { level: 1 })).toContainText('¿Viene buena o mala la campaña de soja?');
	await expect(page.locator('.hero img.base')).toBeVisible();

	// El mapa y los datos se cargan al montar el monitor.
	await expect(page.locator('#monitor canvas.maplibregl-canvas')).toBeVisible({ timeout: 20_000 });
	await expect(page.locator('#monitor .titular')).toContainText('Viene');

	await page.getByPlaceholder(/Buscar/).fill('Pergamino (Buenos Aires)');
	await page.getByPlaceholder(/Buscar/).press('Enter');
	await expect(page.locator('.panel h3')).toHaveText('Pergamino');
	await expect(page.locator('.panel svg').first()).toBeVisible();

	// El botón de la sequía abre el monitor en 2022/2023.
	await page.getByRole('button', { name: 'Ver cómo se vio la sequía' }).click();
	await expect(page.locator('#monitor select')).toHaveValue('2022/2023');

	expect(errores).toEqual([]);
});

test('el gráfico de acierto y las tablas alternativas están', async ({ page }) => {
	await page.goto('/#funciona');
	await expect(page.locator('#funciona svg').first()).toBeVisible();
	await page.getByText('Ver los datos como tabla').click();
	await expect(page.locator('#funciona table').first()).toBeVisible();
});
