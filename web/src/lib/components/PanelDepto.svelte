<script lang="ts">
	import { COLOR, ETIQUETA, ICONO, type Clase } from '../clases';
	import { anomaliaPct, fechaDecada, fechaLarga, kgha, pct } from '../formato';
	import type { Monitor } from '../datos';
	import CurvaNdvi from './CurvaNdvi.svelte';

	interface Props {
		datos: Monitor;
		depto: string | null;
		campania: string;
		decada: number;
		clase: { clase: Clase; an: number | null } | undefined;
		destacados: { id: string; nombre: string; an: number; clase: Clase }[];
		onelegir: (id: string) => void;
	}
	let { datos, depto, campania, decada, clase, destacados, onelegir }: Props = $props();

	const serie = $derived(depto ? datos.series[campania]?.[depto] : undefined);
	const k = $derived(clase?.clase ?? 'sin_dato');
	const cierre = $derived(
		serie?.base != null && serie.pred != null
			? [
					{ nombre: 'Promedio histórico del departamento', valor: serie.base, tono: 'base' },
					{ nombre: 'Estimación del modelo', valor: serie.pred, tono: 'modelo' },
					...(serie.y != null ? [{ nombre: 'Oficial (MAGyP)', valor: serie.y, tono: 'oficial' }] : [])
				]
			: null
	);
	const tope = $derived(cierre ? Math.max(...cierre.map((c) => c.valor)) : 1);
	// Ejemplos para empezar: el piloto del proyecto y dos deptos de otras zonas.
	const ejemplos = $derived(['06623', '06063', '14063'].filter((id) => datos.deptos[id]));
</script>

<aside class="panel tarjeta" aria-live="polite">
	{#if !depto || !serie}
		<div class="vacio">
			<p class="ojo">Departamento</p>
			<h3>Elegí uno en el mapa</h3>
			<p>O buscalo por nombre. Vas a ver cómo viene su curva de verdor frente a la de otras campañas y cuánto rindió.</p>
			<div class="ejemplos">
				{#each ejemplos as id (id)}
					<button class="boton secundario chico" onclick={() => onelegir(id)}>{datos.deptos[id].n}</button>
				{/each}
			</div>
			{#if destacados.length}
				<h4>Los que más se alejan de lo normal a esta fecha</h4>
				<ol class="destacados">
					{#each destacados as d (d.id)}
						<li>
							<button class="enlace" onclick={() => onelegir(d.id)}><span aria-hidden="true">{ICONO[d.clase]}</span> {d.nombre}</button>
							<span class="cifra">{anomaliaPct(d.an)}</span>
						</li>
					{/each}
				</ol>
			{/if}
		</div>
	{:else}
		<header>
			<p class="ojo">{datos.deptos[depto]?.p}</p>
			<h3>{datos.deptos[depto]?.n}</h3>
		</header>

		<div class="veredicto" style:--c={COLOR[k]}>
			<span class="icono" aria-hidden="true">{ICONO[k]}</span>
			<div>
				<strong>{ETIQUETA[k]}</strong>
				{#if k === 'pocos'}
					<p>Hay menos de {datos.min_puntos} píxeles de soja en esta campaña: el dato es poco confiable.</p>
				{:else if clase?.an != null}
					<p>
						{anomaliaPct(clase.an)} frente a lo habitual al {fechaLarga(fechaDecada(campania, datos.decadas[decada]), false)}.
					</p>
				{:else}
					<p>No hay otras campañas contra las que comparar.</p>
				{/if}
			</div>
		</div>

		<CurvaNdvi {datos} {depto} {campania} {decada} clase={k} />

		{#if cierre}
			<section class="cierre" aria-labelledby="t-cierre">
				<h4 id="t-cierre">Rinde al cierre de la campaña {campania.replace('/20', '/')}</h4>
				<ul>
					{#each cierre as c (c.nombre)}
						<li>
							<span class="nombre">{c.nombre}</span>
							<span class="barra"><span class="relleno {c.tono}" style:width="{(100 * c.valor) / tope}%"></span></span>
							<span class="valor">{kgha(c.valor)}</span>
						</li>
					{/each}
				</ul>
				<p class="nota">
					{#if serie.y != null}
						La estimación usa la campaña completa y se calculó sin conocer el rinde de esta campaña. Oficial contra el promedio histórico:
						{anomaliaPct(100 * (serie.y / serie.base! - 1))}.
					{:else}
						Estimación provisoria: el MAGyP todavía no publicó el rinde oficial de esta campaña. Estimado contra el promedio histórico:
						{anomaliaPct(100 * (serie.pred! / serie.base! - 1))}.
					{/if}
				</p>
			</section>
		{/if}

		<details>
			<summary>Ver los datos de la curva como tabla</summary>
			<table>
				<thead><tr><th>Década</th><th>Esta campaña</th><th>Anomalía</th></tr></thead>
				<tbody>
					{#each datos.decadas as d, i (d)}
						<tr class:futuro={i > decada}>
							<td>{fechaLarga(fechaDecada(campania, d), false)}</td>
							<td>{serie.ndvi[i]?.toFixed(2).replace('.', ',') ?? '–'}</td>
							<td>{serie.an[i] != null ? anomaliaPct(serie.an[i]!) : '–'}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</details>
	{/if}
</aside>

<style>
	.panel {
		padding: 1.25rem;
		display: grid;
		gap: 1rem;
		align-content: start;
		min-height: 100%;
	}
	header {
		display: grid;
		gap: 0.3rem;
	}
	header h3 {
		font-size: 1.6rem;
	}
	.destacados {
		margin: 0;
		padding: 0;
		list-style: none;
		display: grid;
		gap: 0.2rem;
		font-size: 0.9rem;
	}
	.destacados li {
		display: flex;
		justify-content: space-between;
		gap: 0.75rem;
		padding: 0.3rem 0;
		border-bottom: 1px solid var(--line);
	}
	.cifra {
		font-variant-numeric: tabular-nums;
		font-weight: 600;
	}
	.enlace {
		appearance: none;
		border: 0;
		background: none;
		padding: 0;
		color: var(--ink);
		text-align: left;
		cursor: pointer;
	}
	.enlace:hover {
		color: var(--acento);
		text-decoration: underline;
	}
	.vacio {
		display: grid;
		gap: 0.75rem;
		color: var(--ink-2);
	}
	.ejemplos {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}
	.veredicto {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: 0.8rem;
		align-items: center;
		padding: 0.7rem 0.9rem;
		border-radius: 8px;
		background: color-mix(in srgb, var(--c) 14%, white);
		border-left: 4px solid var(--c);
	}
	.icono {
		font-size: 1.4rem;
		line-height: 1;
		color: var(--ink);
	}
	.veredicto p {
		font-size: 0.9rem;
		color: var(--ink-2);
	}
	h4 {
		margin: 0 0 0.6rem;
		font: 600 0.95rem/1.3 var(--sans);
	}
	.cierre ul {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		gap: 0.55rem;
	}
	.cierre li {
		display: grid;
		grid-template-columns: 1fr auto;
		gap: 0.15rem 0.75rem;
		font-size: 0.85rem;
	}
	.barra {
		grid-column: 1 / -1;
		order: 3;
		height: 8px;
		border-radius: 4px;
		background: #efede7;
		overflow: hidden;
	}
	.relleno {
		display: block;
		height: 100%;
		border-radius: 4px;
	}
	.base {
		background: #aeb3ba;
	}
	.modelo {
		background: var(--acento);
	}
	.oficial {
		background: var(--ink);
	}
	.valor {
		font-variant-numeric: tabular-nums;
		font-weight: 600;
	}
	.nota {
		margin-top: 0.7rem;
		font-size: 0.78rem;
		color: var(--muted);
	}
	details {
		font-size: 0.85rem;
	}
	summary {
		cursor: pointer;
		color: var(--acento);
	}
	table {
		width: 100%;
		margin-top: 0.5rem;
		border-collapse: collapse;
		font-variant-numeric: tabular-nums;
	}
	th,
	td {
		padding: 0.25rem 0.4rem;
		text-align: left;
		border-bottom: 1px solid var(--line);
	}
	.futuro {
		color: var(--muted);
	}
</style>
