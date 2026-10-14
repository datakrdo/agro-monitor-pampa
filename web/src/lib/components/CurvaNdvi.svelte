<script lang="ts">
	import * as Plot from '@observablehq/plot';
	import { COLOR, cuantil, type Clase } from '../clases';
	import { fechaDecada, fechaLarga, mesCorto } from '../formato';
	import type { Monitor } from '../datos';

	let { datos, depto, campania, decada, clase }: { datos: Monitor; depto: string; campania: string; decada: number; clase: Clase } = $props();
	let ancho = $state(420);
	let host: HTMLDivElement;

	const fmt = (v: number | null | undefined) => (v == null ? '–' : v.toFixed(2).replace('.', ','));

	/** Una fila por década: la campaña elegida y el rango (p10-mediana-p90) de las otras campañas del depto. */
	function filas(d: Monitor, id: string, c: string) {
		const actual = d.series[c]?.[id]?.ndvi ?? [];
		const otras = Object.entries(d.series).filter(([k]) => k !== c).map(([, s]) => s[id]?.ndvi).filter((x): x is (number | null)[] => !!x);
		return d.decadas.map((mmdd, i) => {
			const h = otras.map((o) => o[i]).filter((v): v is number => v != null);
			return {
				i, fecha: fechaDecada(c, mmdd), actual: actual[i] ?? null,
				p10: h.length > 1 ? cuantil(h, 0.1) : null, med: h.length ? cuantil(h, 0.5) : null, p90: h.length > 1 ? cuantil(h, 0.9) : null
			};
		});
	}
	const tabla = $derived(filas(datos, depto, campania));

	$effect(() => {
		const hasta = tabla.filter((r) => r.i <= decada && r.actual !== null);
		const hoy = tabla[decada];
		const color = clase === 'normal' || clase === 'pocos' || clase === 'sin_dato' ? '#5f6670' : COLOR[clase];
		const g = Plot.plot({
			width: ancho, height: 230, marginLeft: 36, marginRight: 12, marginBottom: 28,
			style: { background: 'transparent', fontSize: '12px', fontFamily: 'inherit', color: '#646c75', overflow: 'visible' },
			x: { type: 'utc', label: null, ticks: 'month', tickFormat: (d: Date) => mesCorto(d) },
			y: { domain: [0, 1], label: null, grid: true, ticks: 5, tickFormat: (d: number) => String(d).replace('.', ',') },
			marks: [
				Plot.areaY(tabla.filter((r) => r.p10 !== null), { x: 'fecha', y1: 'p10', y2: 'p90', fill: '#8a9099', fillOpacity: 0.2 }),
				Plot.lineY(tabla.filter((r) => r.med !== null), { x: 'fecha', y: 'med', stroke: '#6b737c', strokeDasharray: '4 3', strokeWidth: 1.4 }),
				Plot.lineY(hasta, { x: 'fecha', y: 'actual', stroke: color, strokeWidth: 2.8 }),
				hoy ? Plot.ruleX([hoy.fecha], { stroke: '#1b1f23', strokeOpacity: 0.35 }) : null,
				hasta.length ? Plot.dot(hasta.slice(-1), { x: 'fecha', y: 'actual', r: 5, fill: color, stroke: '#fff', strokeWidth: 2 }) : null,
				Plot.tip(hasta, Plot.pointerX({
					x: 'fecha', y: 'actual',
					title: (r: (typeof tabla)[number]) => `${fechaLarga(r.fecha, false)}\nEsta campaña: ${fmt(r.actual)}\nTípico: ${fmt(r.med)}`
				}))
			]
		});
		host.replaceChildren(g);
	});
</script>

<div bind:this={host} bind:clientWidth={ancho} class="curva" role="img" aria-label="Curva de verdor (NDVI) de la campaña elegida contra el rango de las otras campañas"></div>
<ul class="leyenda">
	<li><span class="trazo" style:background={clase === 'mala' || clase === 'buena' ? COLOR[clase] : '#5f6670'}></span>Esta campaña, hasta la fecha elegida</li>
	<li><span class="trazo punteado"></span>Mediana de las otras campañas</li>
	<li><span class="banda"></span>Rango típico (10%–90%)</li>
</ul>

<style>
	.curva {
		min-height: 230px;
	}
	.leyenda {
		display: flex;
		flex-wrap: wrap;
		gap: 0.3rem 1.1rem;
		margin: 0.4rem 0 0;
		padding: 0;
		list-style: none;
		font-size: 0.8rem;
		color: var(--muted);
	}
	li {
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
	}
	.trazo {
		width: 18px;
		height: 3px;
		border-radius: 2px;
	}
	.punteado {
		background: repeating-linear-gradient(90deg, #6b737c 0 4px, transparent 4px 7px);
		height: 2px;
	}
	.banda {
		width: 18px;
		height: 10px;
		background: rgb(138 144 153 / 0.25);
	}
</style>
