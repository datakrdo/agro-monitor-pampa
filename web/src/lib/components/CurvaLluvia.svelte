<script lang="ts">
	import * as Plot from '@observablehq/plot';
	import { cuantil } from '../clases';
	import { fechaDecada, formatos } from '../formato';
	import { idioma } from '../i18n';
	import type { Monitor } from '../datos';

	let { datos, depto, campania, decada }: { datos: Monitor; depto: string; campania: string; decada: number } = $props();
	let ancho = $state(420);
	let host = $state<HTMLDivElement>();
	const AZUL = '#2f6fa3';

	const T = {
		es: {
			h4: 'Lluvia acumulada', aria: 'Lluvia acumulada de la campaña elegida contra el rango de las otras campañas',
			l1: 'Esta campaña, hasta la fecha elegida', l2: 'Mediana de las otras campañas', l3: 'Rango típico (10%–90%)', actual: 'Esta campaña', tipico: 'Típico',
			resumen: (mm: string, fecha: string) => `Llovieron ${mm} mm hasta el ${fecha}`, frente: (a: string) => ` · ${a} frente a lo habitual`
		},
		en: {
			h4: 'Cumulative rainfall', aria: 'Cumulative rainfall of the chosen campaign against the range of the other campaigns',
			l1: 'This campaign, up to the chosen date', l2: 'Median of the other campaigns', l3: 'Typical range (10%–90%)', actual: 'This campaign', tipico: 'Typical',
			resumen: (mm: string, fecha: string) => `${mm} mm of rain up to ${fecha}`, frente: (a: string) => ` · ${a} versus usual`
		}
	};
	const t = $derived(T[idioma()]);
	const f = $derived(formatos(idioma()));

	/** Una fila por década: lluvia de la campaña elegida y rango (p10-mediana-p90) de las otras campañas del depto. */
	const tabla = $derived.by(() => {
		const actual = datos.series[campania]?.[depto]?.ll ?? [];
		const otras = Object.entries(datos.series).filter(([k]) => k !== campania).map(([, s]) => s[depto]?.ll).filter((x): x is (number | null)[] => !!x);
		return datos.decadas.map((mmdd, i) => {
			const h = otras.map((o) => o[i]).filter((v): v is number => v != null);
			return {
				i, fecha: fechaDecada(campania, mmdd), actual: actual[i] ?? null,
				p10: h.length > 1 ? cuantil(h, 0.1) : null, med: h.length ? cuantil(h, 0.5) : null, p90: h.length > 1 ? cuantil(h, 0.9) : null
			};
		});
	});
	const hoy = $derived(tabla[decada]);
	const hay = $derived(tabla.some((r) => r.actual !== null));
	const dif = $derived(hoy?.actual != null && hoy.med ? 100 * (hoy.actual / hoy.med - 1) : null);

	$effect(() => {
		const hasta = tabla.filter((r) => r.i <= decada && r.actual !== null);
		const tope = Math.max(10, ...tabla.map((r) => Math.max(r.p90 ?? 0, r.actual ?? 0)));
		if (!host) return;
		const f = formatos(idioma());
		const t = T[idioma()];
		const g = Plot.plot({
			width: ancho, height: 170, marginLeft: 36, marginRight: 12, marginBottom: 28,
			style: { background: 'transparent', fontSize: '12px', fontFamily: 'inherit', color: '#646c75', overflow: 'visible' },
			x: { type: 'utc', label: null, ticks: 'month', tickFormat: (d: Date) => f.mesCorto(d) },
			y: { domain: [0, tope], label: null, grid: true, ticks: 4 },
			marks: [
				Plot.areaY(tabla.filter((r) => r.p10 !== null), { x: 'fecha', y1: 'p10', y2: 'p90', fill: '#8a9099', fillOpacity: 0.2 }),
				Plot.lineY(tabla.filter((r) => r.med !== null), { x: 'fecha', y: 'med', stroke: '#6b737c', strokeDasharray: '4 3', strokeWidth: 1.4 }),
				Plot.lineY(hasta, { x: 'fecha', y: 'actual', stroke: AZUL, strokeWidth: 2.8 }),
				hoy ? Plot.ruleX([hoy.fecha], { stroke: '#1b1f23', strokeOpacity: 0.35 }) : null,
				hasta.length ? Plot.dot(hasta.slice(-1), { x: 'fecha', y: 'actual', r: 5, fill: AZUL, stroke: '#fff', strokeWidth: 2 }) : null,
				Plot.tip(hasta, Plot.pointerX({
					x: 'fecha', y: 'actual',
					title: (r: (typeof tabla)[number]) => `${f.fechaLarga(r.fecha, false)}\n${t.actual}: ${f.dec(r.actual!)} mm\n${t.tipico}: ${r.med == null ? '–' : f.dec(r.med, 0, 0)} mm`
				}))
			]
		});
		host.replaceChildren(g);
	});
</script>

{#if hay}
	<section class="lluvia" aria-labelledby="t-lluvia">
		<h4 id="t-lluvia">{t.h4}</h4>
		{#if hoy?.actual != null}
			<p class="resumen">
				<strong>{t.resumen(f.dec(hoy.actual, 0, 0), f.fechaLarga(hoy.fecha, false))}</strong>{dif != null ? t.frente(f.anomaliaPct(dif)) : ''}
			</p>
		{/if}
		<div bind:this={host} bind:clientWidth={ancho} class="curva" role="img" aria-label={t.aria}></div>
		<ul class="leyenda">
			<li><span class="trazo"></span>{t.l1}</li>
			<li><span class="trazo punteado"></span>{t.l2}</li>
			<li><span class="banda"></span>{t.l3}</li>
		</ul>
	</section>
{/if}

<style>
	h4 {
		margin: 0 0 0.3rem;
		font: 600 0.95rem/1.3 var(--sans);
	}
	.resumen {
		margin: 0 0 0.3rem;
		font-size: 0.88rem;
		color: var(--ink-2);
	}
	.curva {
		min-height: 170px;
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
		background: #2f6fa3;
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
