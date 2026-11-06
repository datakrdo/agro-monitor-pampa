<script lang="ts">
	import { onMount } from 'svelte';
	import type { FeatureCollection, Geometry, Polygon } from 'geojson';
	import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
	import type { ExpressionSpecification, Map as MapaMapLibre } from 'maplibre-gl';
	import { colores, ETIQUETA, ICONO, type Clase } from '../clases';
	import { esOscuro, tema } from '../estado.svelte';
	import { formatos, token } from '../formato';
	import { idioma } from '../i18n';

	interface Props {
		geojson: FeatureCollection;
		clases: Record<string, { clase: Clase; an: number | null }>;
		nombres: Record<string, { n: string; p: string }>;
		seleccionado: string | null;
		onelegir: (id: string) => void;
	}
	let { geojson, clases, nombres, seleccionado, onelegir }: Props = $props();

	const L = $derived(idioma());
	const T = {
		es: {
			ctrl: 'Usá Ctrl + scroll para hacer zoom en el mapa', cmd: 'Usá ⌘ + scroll para hacer zoom en el mapa', dedos: 'Usá dos dedos para mover el mapa',
			aria: 'Mapa de departamentos coloreado según cómo viene la campaña. Hay una tabla equivalente debajo.', cargando: 'Cargando mapa…'
		},
		en: {
			ctrl: 'Use Ctrl + scroll to zoom the map', cmd: 'Use ⌘ + scroll to zoom the map', dedos: 'Use two fingers to move the map',
			aria: 'Map of departments coloured by how the campaign is going. An equivalent table is below.', cargando: 'Loading map…'
		}
	};
	const t = $derived(T[L]);
	const ESTILOS = { claro: 'https://tiles.openfreemap.org/styles/positron', oscuro: 'https://tiles.openfreemap.org/styles/dark' };
	// Si el mapa base no carga, la coropleta se ve igual sobre un fondo liso.
	const sinBase = () => ({ version: 8 as const, sources: {}, layers: [{ id: 'fondo', type: 'background' as const, paint: { 'background-color': token('--mapa-fondo') } }] });
	const cargarEstilo = (oscuro: boolean) => fetch(ESTILOS[oscuro ? 'oscuro' : 'claro']).then((r) => (r.ok ? r.json() : sinBase())).catch(sinBase);
	const FUENTE = 'deptos';

	let contenedor: HTMLDivElement;
	let mapa: MapaMapLibre | undefined;
	let listo = $state(false);
	let primera = true;
	let anterior: string | null = null;
	let estiloOscuro = false;

	const duracion = () => (matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 700);

	function limites(geom: Geometry): [[number, number], [number, number]] {
		const pares: number[][] = [];
		const juntar = (c: unknown): void => {
			if (typeof (c as number[])[0] === 'number') pares.push(c as number[]);
			else (c as unknown[]).forEach(juntar);
		};
		juntar((geom as Polygon).coordinates);
		const lons = pares.map((p) => p[0]);
		const lats = pares.map((p) => p[1]);
		return [[Math.min(...lons), Math.min(...lats)], [Math.max(...lons), Math.max(...lats)]];
	}
	const region = (): [[number, number], [number, number]] => {
		const todos = geojson.features.map((f) => limites(f.geometry));
		return [[Math.min(...todos.map((b) => b[0][0])), Math.min(...todos.map((b) => b[0][1]))], [Math.max(...todos.map((b) => b[1][0])), Math.max(...todos.map((b) => b[1][1]))]];
	};

	function hachurado(): ImageData {
		const t = 8;
		const c = document.createElement('canvas');
		c.width = c.height = t;
		const g = c.getContext('2d')!;
		g.strokeStyle = token('--hachura');
		g.lineWidth = 1.2;
		g.beginPath();
		for (const d of [-t, 0, t]) {
			g.moveTo(d, t);
			g.lineTo(d + t, 0);
		}
		g.stroke();
		return g.getImageData(0, 0, t, t);
	}

	onMount(() => {
		let destruido = false;
		(async () => {
			const [maplibregl] = await Promise.all([import('maplibre-gl'), import('maplibre-gl/dist/maplibre-gl.css')]);
			maplibregl.setWorkerUrl(workerUrl);
			estiloOscuro = esOscuro();
			const estilo = await cargarEstilo(estiloOscuro);
			if (destruido) return;
			const m = new maplibregl.Map({
				container: contenedor,
				style: estilo,
				bounds: region(),
				fitBoundsOptions: { padding: 12 },
				cooperativeGestures: true,
				locale: {
					'CooperativeGesturesHandler.WindowsHelpText': t.ctrl,
					'CooperativeGesturesHandler.MacHelpText': t.cmd,
					'CooperativeGesturesHandler.MobileHelpText': t.dedos
				}
			});
			m.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
			mapa = m;

			// Fuente y capas propias; se vuelven a poner cada vez que cambia el estilo base (tema).
			const capas = () => {
				const pal = colores(estiloOscuro);
				if (!m.hasImage('hachurado')) m.addImage('hachurado', hachurado(), { pixelRatio: 2 });
				m.addSource(FUENTE, { type: 'geojson', data: geojson, promoteId: 'depto_id' });
				const bajoEtiquetas = m.getStyle().layers.find((l) => l.type === 'symbol')?.id;
				// El estilo oscuro trae etiquetas gris 101 con halo negro: sobre la coropleta no se leen.
				if (estiloOscuro) {
					for (const l of m.getStyle().layers) {
						if (l.type !== 'symbol' || !l.layout?.['text-field']) continue;
						m.setPaintProperty(l.id, 'text-color', token('--ink-2'));
						m.setPaintProperty(l.id, 'text-halo-color', token('--bg'));
					}
				}
				const color = ['match', ['feature-state', 'clase'], 'mala', pal.mala, 'normal', pal.normal, 'buena', pal.buena, 'pocos', pal.pocos, pal.sin_dato] as ExpressionSpecification;
				m.addLayer({ id: 'relleno', type: 'fill', source: FUENTE, paint: { 'fill-color': color, 'fill-opacity': 0.82 } }, bajoEtiquetas);
				m.addLayer({ id: 'pocos', type: 'fill', source: FUENTE, paint: { 'fill-pattern': 'hachurado', 'fill-opacity': ['case', ['==', ['feature-state', 'clase'], 'pocos'], 1, 0] } }, bajoEtiquetas);
				m.addLayer({ id: 'borde', type: 'line', source: FUENTE, paint: { 'line-color': token('--bg'), 'line-width': 0.6, 'line-opacity': 0.9 } }, bajoEtiquetas);
				m.addLayer({
					id: 'resalte', type: 'line', source: FUENTE,
					paint: {
						'line-color': token('--ink'),
						'line-width': ['case', ['boolean', ['feature-state', 'sel'], false], 3, ['boolean', ['feature-state', 'hover'], false], 1.8, 0]
					}
				});
			};

			m.on('load', () => {
				capas();

				const aviso = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 8, className: 'aviso-depto' });
				let sobre: string | null = null;
				m.on('mousemove', 'relleno', (e) => {
					const id = e.features?.[0]?.properties?.depto_id as string | undefined;
					if (!id) return;
					m.getCanvas().style.cursor = 'pointer';
					if (sobre !== id) {
						if (sobre) m.setFeatureState({ source: FUENTE, id: sobre }, { hover: false });
						m.setFeatureState({ source: FUENTE, id }, { hover: true });
						sobre = id;
					}
					const c = clases[id];
					const el = document.createElement('div');
					const t = document.createElement('strong');
					t.textContent = `${nombres[id]?.n ?? id} `;
					const p = document.createElement('span');
					p.textContent = `(${nombres[id]?.p ?? ''})`;
					const linea = document.createElement('div');
					const k = c?.clase ?? 'sin_dato';
					linea.textContent = `${ICONO[k]} ${ETIQUETA[L][k]}${c && c.an !== null && k !== 'pocos' ? ` · ${formatos(L).anomaliaPct(c.an)}` : ''}`;
					el.append(t, p, linea);
					aviso.setLngLat(e.lngLat).setDOMContent(el).addTo(m);
				});
				m.on('mouseleave', 'relleno', () => {
					m.getCanvas().style.cursor = '';
					if (sobre) m.setFeatureState({ source: FUENTE, id: sobre }, { hover: false });
					sobre = null;
					aviso.remove();
				});
				m.on('click', 'relleno', (e) => {
					const id = e.features?.[0]?.properties?.depto_id as string | undefined;
					if (id) onelegir(id);
				});
				// Cambio de tema: el estilo nuevo trae sus propias capas, así que se re-arma todo y se re-aplican los estados.
				m.on('style.load', () => {
					capas();
					for (const f of geojson.features) {
						const id = f.properties?.depto_id as string;
						m.setFeatureState({ source: FUENTE, id }, { clase: clases[id]?.clase ?? 'sin_dato' });
					}
					if (seleccionado) m.setFeatureState({ source: FUENTE, id: seleccionado }, { sel: true });
				});
				listo = true;
			});
		})();
		return () => {
			destruido = true;
			mapa?.remove();
		};
	});

	// Color de cada departamento según la campaña y la fecha elegidas.
	$effect(() => {
		if (!listo || !mapa) return;
		for (const f of geojson.features) {
			const id = f.properties?.depto_id as string;
			mapa.setFeatureState({ source: FUENTE, id }, { clase: clases[id]?.clase ?? 'sin_dato' });
		}
	});

	// Tema claro/oscuro: cambia el mapa base y los colores de las capas.
	$effect(() => {
		const o = tema.oscuro;
		if (!listo || !mapa || o === estiloOscuro) return;
		estiloOscuro = o;
		const m = mapa;
		cargarEstilo(o).then((est) => estiloOscuro === o && m.setStyle(est));
	});

	// Contorno y zoom del departamento elegido; sin selección, vuelve a toda la región.
	$effect(() => {
		if (!listo || !mapa) return;
		const sel = seleccionado;
		if (anterior) mapa.setFeatureState({ source: FUENTE, id: anterior }, { sel: false });
		if (sel) {
			mapa.setFeatureState({ source: FUENTE, id: sel }, { sel: true });
			const f = geojson.features.find((x) => x.properties?.depto_id === sel);
			if (f) mapa.fitBounds(limites(f.geometry), { padding: 60, maxZoom: 9, duration: duracion() });
		} else if (!primera) {
			mapa.fitBounds(region(), { padding: 12, duration: duracion() });
		}
		primera = false;
		anterior = sel;
	});
</script>

<div class="mapa" role="group" aria-label={t.aria}>
	<div bind:this={contenedor} class="lienzo"></div>
	{#if !listo}<p class="cargando">{t.cargando}</p>{/if}
</div>

<style>
	.mapa {
		position: relative;
		border: 1px solid var(--line);
		border-radius: var(--radio);
		overflow: hidden;
		background: var(--mapa-fondo);
	}
	.lienzo {
		height: clamp(380px, 62vh, 600px);
	}
	.cargando {
		position: absolute;
		inset: 0;
		display: grid;
		place-items: center;
		color: var(--muted);
		pointer-events: none;
	}
	:global(.aviso-depto .maplibregl-popup-content) {
		padding: 0.5rem 0.7rem;
		font: 0.85rem/1.35 var(--sans);
		color: var(--ink);
		background: var(--surface);
		border-radius: 8px;
	}
	:global(.aviso-depto .maplibregl-popup-tip) {
		border-top-color: var(--surface);
		border-bottom-color: var(--surface);
	}
	:global(.mapa .maplibregl-ctrl-group) {
		background: var(--surface);
		border: 1px solid var(--borde-fuerte);
		box-shadow: none;
	}
	:global(.mapa .maplibregl-ctrl-group button + button) {
		border-top-color: var(--line);
	}
	/* Los íconos de MapLibre son negros: en oscuro se invierten. */
	:global(:root[data-tema='oscuro'] .mapa .maplibregl-ctrl-icon) {
		filter: invert(1);
	}
	@media (prefers-color-scheme: dark) {
		:global(:root:not([data-tema='claro']):not([data-tema='oscuro']) .mapa .maplibregl-ctrl-icon) {
			filter: invert(1);
		}
	}
	:global(.mapa .maplibregl-ctrl-group button:active) {
		background: var(--surface-3);
	}
	:global(.mapa .maplibregl-ctrl-attrib) {
		background: var(--vidrio);
		color: var(--muted);
	}
	:global(.mapa .maplibregl-ctrl-attrib a) {
		color: var(--ink-2);
	}
</style>
