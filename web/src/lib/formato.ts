import type { Idioma } from './i18n';

const MESES: Record<Idioma, string[]> = {
	es: ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'],
	en: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
};
const LOCALE: Record<Idioma, string> = { es: 'es-AR', en: 'en-US' };

/** 'MM-DD' de una década de la campaña '2022/2023' (sembrada en 2022) como fecha UTC. Nov-dic caen en el primer año. */
export function fechaDecada(campania: string, mmdd: string): Date {
	const [m, d] = mmdd.split('-').map(Number);
	const anio = Number(campania.split('/')[0]) + (m >= 7 ? 0 : 1);
	return new Date(Date.UTC(anio, m - 1, d));
}

export function nombreMes(f: Date, idioma: Idioma = 'es'): string {
	return MESES[idioma][f.getUTCMonth()];
}

/** '1 de diciembre de 2022' / 'December 1, 2022' (o sin año). */
export function fechaLarga(f: Date, conAnio = true, idioma: Idioma = 'es'): string {
	const d = f.getUTCDate();
	const m = nombreMes(f, idioma);
	const a = f.getUTCFullYear();
	if (idioma === 'en') return conAnio ? `${m} ${d}, ${a}` : `${m} ${d}`;
	return `${d} de ${m}${conAnio ? ` de ${a}` : ''}`;
}

export function mesCorto(f: Date, idioma: Idioma = 'es'): string {
	return nombreMes(f, idioma).slice(0, 3);
}

/** Número con el separador decimal del idioma (0,5 / 0.5). */
export function dec(x: number, idioma: Idioma = 'es', min = 0, max = 3): string {
	return x.toLocaleString(LOCALE[idioma], { minimumFractionDigits: min, maximumFractionDigits: max });
}

/** 0,77 -> '77%'. */
export function pct(x: number, decimales = 0, idioma: Idioma = 'es'): string {
	return `${dec(x * 100, idioma, decimales, decimales)}%`;
}

/** Anomalía ya en %: -12,4 -> '−12,4%'. */
export function anomaliaPct(x: number, idioma: Idioma = 'es'): string {
	return `${x < 0 ? '−' : x > 0 ? '+' : ''}${dec(Math.abs(x), idioma, 1, 1)}%`;
}

export function kgha(x: number, idioma: Idioma = 'es'): string {
	return `${dec(Math.round(x), idioma)} kg/ha`;
}

/** Los formateadores de arriba con el idioma ya fijado, para usar en las plantillas. */
export const formatos = (i: Idioma) => ({
	fechaLarga: (f: Date, conAnio = true) => fechaLarga(f, conAnio, i),
	mesCorto: (f: Date) => mesCorto(f, i),
	nombreMes: (f: Date) => nombreMes(f, i),
	dec: (x: number, min = 0, max = 3) => dec(x, i, min, max),
	pct: (x: number, decimales = 0) => pct(x, decimales, i),
	anomaliaPct: (x: number) => anomaliaPct(x, i),
	kgha: (x: number) => kgha(x, i)
});
