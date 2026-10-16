import { describe, expect, it } from 'vitest';
import { clasificar, cuantil, veredicto } from './clases';
import { anomaliaPct, fechaDecada, fechaLarga, kgha, mesCorto, pct } from './formato';

describe('clasificar', () => {
	it('usa el umbral sin incluirlo', () => {
		expect(clasificar(-5.1, 300, 5, 30)).toBe('mala');
		expect(clasificar(-5, 300, 5, 30)).toBe('normal');
		expect(clasificar(5, 300, 5, 30)).toBe('normal');
		expect(clasificar(5.1, 300, 5, 30)).toBe('buena');
	});
	it('los deptos con pocos píxeles no se clasifican aunque tengan anomalía', () => {
		expect(clasificar(-40, 12, 5, 30)).toBe('pocos');
	});
	it('sin anomalía es sin_dato', () => {
		expect(clasificar(null, 300, 5, 30)).toBe('sin_dato');
	});
});

describe('veredicto', () => {
	it('es la clase de la mediana', () => {
		expect(veredicto([-30, -20, -10, 2, 3], 5)).toBe('mala');
		expect(veredicto([-30, 1, 2, 3, 40], 5)).toBe('normal');
		expect(veredicto([], 5)).toBeNull();
	});
});

describe('cuantil', () => {
	it('interpola como pandas', () => {
		expect(cuantil([1, 2, 3, 4], 0.5)).toBe(2.5);
		expect(cuantil([1, 2, 3, 4, 5], 0.1)).toBeCloseTo(1.4);
		expect(cuantil([7], 0.9)).toBe(7);
	});
});

describe('formato', () => {
	it('asigna el año de la campaña a cada década', () => {
		expect(fechaLarga(fechaDecada('2022/2023', '12-01'))).toBe('1 de diciembre de 2022');
		expect(fechaLarga(fechaDecada('2022/2023', '01-11'), false)).toBe('11 de enero');
		expect(fechaDecada('2022/2023', '03-01').getUTCFullYear()).toBe(2023);
	});
	it('formatea en inglés', () => {
		expect(fechaLarga(fechaDecada('2022/2023', '12-01'), true, 'en')).toBe('December 1, 2022');
		expect(fechaLarga(fechaDecada('2022/2023', '01-11'), false, 'en')).toBe('January 11');
		expect(mesCorto(fechaDecada('2022/2023', '03-01'), 'en')).toBe('Mar');
		expect(anomaliaPct(-12.44, 'en')).toBe('−12.4%');
		expect(kgha(3456.7, 'en')).toBe('3,457 kg/ha');
		expect(kgha(3456.7)).toBe('3.457 kg/ha');
	});
	it('formatea porcentajes en es-AR', () => {
		expect(pct(0.771)).toBe('77%');
		expect(anomaliaPct(-12.44)).toBe('−12,4%');
		expect(anomaliaPct(3)).toBe('+3,0%');
	});
});
