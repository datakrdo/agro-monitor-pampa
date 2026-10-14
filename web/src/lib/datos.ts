// Forma de los JSON que genera scripts/08_exportar_web.py.
export interface Serie {
	ndvi: (number | null)[];
	an: (number | null)[]; // anomalía a la fecha en % (null si no hay campañas contra las que comparar)
	np: number | null; // píxeles de cultivo muestreados
	y?: number; // rinde oficial MAGyP (kg/ha)
	base?: number; // promedio histórico del depto sin esta campaña
	pred?: number; // estimación del modelo con la campaña completa, fuera de muestra
}

export interface Monitor {
	cultivo: string;
	umbral: number;
	min_puntos: number;
	decadas: string[]; // 'MM-DD'
	campanias: string[];
	deptos: Record<string, { n: string; p: string }>;
	series: Record<string, Record<string, Serie>>;
}

export interface Validacion {
	cultivo: string;
	generado: string;
	umbral: number;
	acierto: {
		decada: number;
		fecha: string;
		marcados: number;
		acierto: number;
		acierto_sin_umbral: number;
		acierto_mala: number;
		acierto_buena: number;
	}[];
	modelo: {
		nombre: string;
		n: number;
		n_campanias: number;
		n_deptos: number;
		rmse_modelo: number;
		rmse_base: number;
		mejora: number;
		campania_peor: string;
		mejora_sin_peor: number;
		acierto_signo: number;
		n_mala: number;
		precision_mala: number;
		mala_era_buena: number;
	};
	por_campania: { campania: string; rmse_modelo: number; rmse_base: number; mejora: number }[];
	sequia: { campania: string; fecha: string; n_deptos: number; deptos_en_rojo: number; deptos_bajo_lo_normal: number; desvio_medio: number };
	hero: {
		depto_id: string;
		depto: string;
		provincia: string;
		campania_mala: string;
		rinde_mala: number;
		base_mala: number;
		pico_mala: number;
		campania_normal: string;
		rinde_normal: number;
		base_normal: number;
		pico_normal: number;
	};
}

export interface HeroImagenes {
	depto_id: string;
	imagenes: { campania: string; anio: number; centro: string; desde: string; hasta: string; archivo: string }[];
}
