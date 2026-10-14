const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];

/** 'MM-DD' de una década de la campaña '2022/2023' (sembrada en 2022) como fecha UTC. Nov-dic caen en el primer año. */
export function fechaDecada(campania: string, mmdd: string): Date {
	const [m, d] = mmdd.split('-').map(Number);
	const anio = Number(campania.split('/')[0]) + (m >= 7 ? 0 : 1);
	return new Date(Date.UTC(anio, m - 1, d));
}

/** '1 de diciembre de 2022' (o sin año). */
export function fechaLarga(f: Date, conAnio = true): string {
	return `${f.getUTCDate()} de ${MESES[f.getUTCMonth()]}${conAnio ? ` de ${f.getUTCFullYear()}` : ''}`;
}

export function mesCorto(f: Date): string {
	return MESES[f.getUTCMonth()].slice(0, 3);
}

/** 0,77 -> '77%' (es-AR). */
export function pct(x: number, decimales = 0): string {
	return `${(x * 100).toLocaleString('es-AR', { minimumFractionDigits: decimales, maximumFractionDigits: decimales })}%`;
}

/** Anomalía ya en %: -12,4 -> '−12,4%'. */
export function anomaliaPct(x: number): string {
	const s = Math.abs(x).toLocaleString('es-AR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
	return `${x < 0 ? '−' : x > 0 ? '+' : ''}${s}%`;
}

export function kgha(x: number): string {
	return `${Math.round(x).toLocaleString('es-AR')} kg/ha`;
}
