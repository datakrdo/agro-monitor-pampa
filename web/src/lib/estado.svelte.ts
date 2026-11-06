// Estado compartido entre el hero (que abre el monitor en la sequía) y el monitor.
export const monitor = $state({
	cultivo: 'soja' as 'soja' | 'trigo',
	campania: '',
	decada: 0,
	depto: null as string | null,
	reproduciendo: false
});

// Tema: 'sistema' sigue prefers-color-scheme; claro/oscuro se recuerdan en localStorage.
// El script de app.html ya puso data-tema antes del primer pintado; acá solo se sincroniza el estado.
export type Modo = 'sistema' | 'claro' | 'oscuro';
export const tema = $state({ oscuro: false, modo: 'sistema' as Modo });

export function esOscuro(): boolean {
	const d = document.documentElement.dataset.tema;
	return d === 'oscuro' || (d !== 'claro' && matchMedia('(prefers-color-scheme: dark)').matches);
}

export function iniciarTema(): () => void {
	try {
		const g = localStorage.getItem('tema');
		if (g === 'claro' || g === 'oscuro') tema.modo = g;
	} catch {}
	tema.oscuro = esOscuro();
	const mq = matchMedia('(prefers-color-scheme: dark)');
	const f = () => (tema.oscuro = esOscuro());
	mq.addEventListener('change', f);
	return () => mq.removeEventListener('change', f);
}

export function ciclarTema(): void {
	const orden: Modo[] = ['sistema', 'claro', 'oscuro'];
	const m = orden[(orden.indexOf(tema.modo) + 1) % 3];
	tema.modo = m;
	if (m === 'sistema') delete document.documentElement.dataset.tema;
	else document.documentElement.dataset.tema = m;
	try {
		if (m === 'sistema') localStorage.removeItem('tema');
		else localStorage.setItem('tema', m);
	} catch {}
	tema.oscuro = esOscuro();
}
