// Cómo se clasifica un departamento en el mapa. El umbral viene de monitor.json
// (UMBRAL_ANOMALIA en src/agro/anomalia.py), nunca se escribe acá.
import type { Idioma } from './i18n';

export type Clase = 'mala' | 'normal' | 'buena' | 'pocos' | 'sin_dato';

export const ETIQUETA: Record<Idioma, Record<Clase, string>> = {
	es: { mala: 'Por debajo de lo normal', normal: 'Normal', buena: 'Por encima de lo normal', pocos: 'Pocos datos', sin_dato: 'Sin dato' },
	en: { mala: 'Below normal', normal: 'Normal', buena: 'Above normal', pocos: 'Little data', sin_dato: 'No data' }
};
export const ICONO: Record<Clase, string> = { mala: '▼', normal: '●', buena: '▲', pocos: '◌', sin_dato: '–' };
// Azul y rojo con un gris neutro en el medio: el par sigue leyéndose bien con daltonismo rojo-verde.
export const COLOR: Record<Clase, string> = {
	mala: '#d03b3b',
	normal: '#d9d7d0',
	buena: '#3987e5',
	pocos: '#ece9e1',
	sin_dato: '#f3f2ee'
};

/** `anomalia` en % contra la mediana histórica a esa fecha; `np` = píxeles de cultivo muestreados. */
export function clasificar(anomalia: number | null, np: number | null, umbral: number, minPuntos: number): Clase {
	if (np !== null && np < minPuntos) return 'pocos';
	if (anomalia === null) return 'sin_dato';
	if (anomalia < -umbral) return 'mala';
	if (anomalia > umbral) return 'buena';
	return 'normal';
}

/** Veredicto de toda la región: la mediana de las anomalías, con el mismo umbral que cada depto. */
export function veredicto(anomalias: number[], umbral: number): 'mala' | 'normal' | 'buena' | null {
	if (!anomalias.length) return null;
	const o = [...anomalias].sort((a, b) => a - b);
	const m = o.length % 2 ? o[(o.length - 1) / 2] : (o[o.length / 2 - 1] + o[o.length / 2]) / 2;
	return clasificar(m, null, umbral, 0) as 'mala' | 'normal' | 'buena';
}

/** Cuantil con interpolación lineal (como numpy/pandas) de una lista sin nulos. */
export function cuantil(valores: number[], q: number): number {
	const o = [...valores].sort((a, b) => a - b);
	const pos = (o.length - 1) * q;
	const i = Math.floor(pos);
	return i + 1 < o.length ? o[i] + (o[i + 1] - o[i]) * (pos - i) : o[i];
}
