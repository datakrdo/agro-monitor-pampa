<script lang="ts">
	import * as Plot from '@observablehq/plot';
	import { tema } from '../estado.svelte';
	import { fechaDecada, formatos, token } from '../formato';
	import { idioma } from '../i18n';
	import type { Validacion } from '../datos';

	let { validacion }: { validacion: Validacion } = $props();
	const acierto = $derived(validacion.acierto);
	const modelo = $derived(validacion.modelo);
	const sequia = $derived(validacion.sequia);
	const por_campania = $derived(validacion.por_campania);
	const T = {
		es: {
			moneda: 'Tirar una moneda: 50%', clara: 'Con señal clara', todos: 'Todos los casos', al: 'Al',
			casosClara: 'Casos con señal clara', ojo: 'La validación', h2: '¿Cuánto acierta?',
			ariaLinea: (d: string, a: string, b: string) => `Línea de acierto según la fecha, de ${a} el ${d} a ${b} al cierre`
		},
		en: {
			moneda: 'Coin flip: 50%', clara: 'Clear signal', todos: 'All cases', al: 'On',
			casosClara: 'Clear-signal cases', ojo: 'Validation', h2: 'How accurate is it?',
			ariaLinea: (d: string, a: string, b: string) => `Accuracy line by date, from ${a} on ${d} to ${b} at the end of the campaign`
		}
	};
	const t = $derived(T[idioma()]);
	const L = $derived(idioma());
	const f = $derived(formatos(L));
	const camp = (c: string) => c.replace('/20', '/');
	const umbral = $derived(f.dec(validacion.umbral));
	const en = (mmdd: string) => acierto.find((a) => a.fecha === mmdd)!;
	// El año es solo de referencia para ubicar nov-may en el eje.
	const REF = '2022/2023';
	const marcas = $derived(validacion.marcas);
	const fl = (mmdd: string) => f.fechaLarga(fechaDecada(REF, mmdd), false);
	let ancho = $state(640);
	let host: HTMLDivElement;

	$effect(() => {
		void tema.oscuro; // redibuja al cambiar de tema
		const f = formatos(idioma());
		const t = T[idioma()];
		const filas = acierto.map((a) => ({ ...a, f: fechaDecada(REF, a.fecha) }));
		const g = Plot.plot({
			width: ancho, height: Math.max(300, Math.min(380, ancho * 0.52)), marginLeft: 44, marginRight: ancho > 520 ? 118 : 12, marginTop: 24,
			style: { background: 'transparent', fontSize: '12px', fontFamily: 'inherit', color: token('--muted'), overflow: 'visible' },
			x: { type: 'utc', label: null, ticks: 'month', tickFormat: (d: Date) => f.mesCorto(d) },
			y: { domain: [Math.floor(Math.min(0.5, ...acierto.map((a) => a.acierto_sin_umbral)) * 10) / 10, Math.ceil(Math.max(...acierto.map((a) => a.acierto)) * 10) / 10], label: null, grid: true, ticks: 5, tickFormat: (d: number) => `${Math.round(d * 100)}%` },
			marks: [
				Plot.ruleY([0.5], { stroke: token('--graf-banda'), strokeDasharray: '4 3' }),
				Plot.text([{ f: filas[0].f }], { x: 'f', y: 0.5, text: () => t.moneda, dy: 11, textAnchor: 'start', fill: token('--muted') }),
				Plot.lineY(filas, { x: 'f', y: 'acierto_sin_umbral', stroke: token('--graf-banda'), strokeWidth: 2 }),
				Plot.lineY(filas, { x: 'f', y: 'acierto', stroke: token('--acento'), strokeWidth: 3 }),
				ancho > 520 ? Plot.text(filas.slice(-1), { x: 'f', y: 'acierto', text: () => t.clara, dx: 8, textAnchor: 'start', fill: token('--acento'), fontWeight: 600 }) : null,
				ancho > 520 ? Plot.text(filas.slice(-1), { x: 'f', y: 'acierto_sin_umbral', text: () => t.todos, dx: 8, dy: 4, textAnchor: 'start', fill: token('--muted') }) : null,
				Plot.dot(filas.filter((r) => marcas.includes(r.fecha)), { x: 'f', y: 'acierto', r: 5, fill: token('--acento'), stroke: token('--punto'), strokeWidth: 2 }),
				Plot.text(filas.filter((r) => marcas.includes(r.fecha)), { x: 'f', y: 'acierto', text: (r: { acierto: number }) => f.pct(r.acierto), dy: -14, fontWeight: 700, fill: token('--ink') }),
				Plot.tip(filas, Plot.pointerX({
					x: 'f', y: 'acierto', fill: token('--surface'), stroke: token('--borde-fuerte'),
					title: (r: (typeof filas)[number]) => `${t.al} ${f.fechaLarga(r.f, false)}\n${t.clara}: ${f.pct(r.acierto)}\n${t.todos}: ${f.pct(r.acierto_sin_umbral)}\n${t.casosClara}: ${f.pct(r.marcados)}`
				}))
			]
		});
		host.replaceChildren(g);
	});
</script>

<section id="funciona" class="seccion alt">
	<div class="contenedor">
		<header class="cabecera">
			<p class="ojo">{t.ojo}</p>
			<h2>{t.h2}</h2>
			<p class="lede">
				{#if L === 'en'}
					We tested the method against MAGyP’s official yields: {modelo.n_campanias} campaigns ({camp(por_campania[0].campania)} to
					{camp(por_campania.at(-1)!.campania)}) and {modelo.n_deptos} departments. Each campaign is evaluated without the method having seen its results.
				{:else}
					Probamos el método con los rindes oficiales del MAGyP: {modelo.n_campanias} campañas ({camp(por_campania[0].campania)} a
					{camp(por_campania.at(-1)!.campania)}) y {modelo.n_deptos} departamentos. Cada campaña se evalúa sin que el método haya visto
					sus resultados.
				{/if}
			</p>
		</header>

		<div class="rejilla">
			<div class="tarjeta grafico">
				<h3>{L === 'en' ? 'The further along the campaign, the more accurate' : 'Cuanto más avanza la campaña, más acierta'}</h3>
				<p class="sub">
					Porcentaje de casos en que el satélite acertó si la campaña terminó por encima o por debajo de lo normal de cada departamento.
				</p>
				<div bind:this={host} bind:clientWidth={ancho} role="img" aria-label={t.ariaLinea(fl(marcas[0]), f.pct(en(marcas[0]).acierto), f.pct(acierto.at(-1)!.acierto))}></div>
				<details>
					<summary>{L === 'en' ? 'View the data as a table' : 'Ver los datos como tabla'}</summary>
					<table>
						<thead><tr><th>{t.al}</th><th>{t.clara}</th><th>{t.todos}</th><th>{t.casosClara}</th></tr></thead>
						<tbody>
							{#each acierto as a (a.fecha)}
								<tr>
									<td>{f.fechaLarga(fechaDecada(REF, a.fecha), false)}</td><td>{f.pct(a.acierto)}</td><td>{f.pct(a.acierto_sin_umbral)}</td><td>{f.pct(a.marcados)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</details>
			</div>

			<div class="datos">
				<div class="tarjeta dato">
					<strong>{f.pct(en(marcas[2]).acierto)}</strong>
					<p>
						{#if L === 'en'}
							accurate on {fl(marcas[2])}, when the anomaly is clear (more than {umbral}% either way: {f.pct(en(marcas[2]).marcados)} of cases).
						{:else}
							acierta al {fl(marcas[2])}, cuando la anomalía es clara (más de {umbral}% hacia un lado: {f.pct(en(marcas[2]).marcados)} de los casos).
						{/if}
					</p>
				</div>
				<div class="tarjeta dato">
					<strong>{f.pct(modelo.precision_mala)}</strong>
					<p>
						{#if L === 'en'}
							of the times the model anticipates a yield more than 10% below normal, it is right ({modelo.n_mala} cases). Only {f.pct(modelo.mala_era_buena)} ended up above.
						{:else}
							de las veces que el modelo anticipa un rinde más de 10% por debajo de lo normal, acierta ({modelo.n_mala} casos). Solo {f.pct(modelo.mala_era_buena)} terminó por encima.
						{/if}
					</p>
				</div>
				<div class="tarjeta dato">
					<strong>{Math.round(modelo.mejora)}%</strong>
					<p>
						{#if L === 'en'}
							less error than using each department’s historical average. Without the {camp(sequia.campania)} drought, the improvement is {Math.round(modelo.mejora_sin_peor)}%.
						{:else}
							menos error que usar el promedio histórico de cada departamento. Sin la sequía de {camp(sequia.campania)}, la mejora es de {Math.round(modelo.mejora_sin_peor)}%.
						{/if}
					</p>
				</div>
			</div>
		</div>

		<div class="tarjeta honesto">
			<h3>{L === 'en' ? 'What you should know' : 'Lo que hay que saber'}</h3>
			<ul>
				{#if L === 'en'}
					<li>
						<strong>Early on it is hard.</strong> On {fl(marcas[0])} accuracy is {f.pct(en(marcas[0]).acierto)}. The {camp(sequia.campania)} drought showed up
						early ({f.pct(sequia.deptos_en_rojo)} of departments in red on {fl(sequia.fecha)}) because it was very severe.
					</li>
					<li><strong>That is {modelo.n_campanias} campaigns and a single drought.</strong> We do not know how it responds in other droughts.</li>
					<li>
						<strong>Near-normal is not judged.</strong> If the satellite sees a campaign within {umbral}% of its history, the map shows it as normal and it counts as neither a hit nor a miss.
					</li>
				{:else}
					<li>
						<strong>Al principio es difícil.</strong> Al {fl(marcas[0])} el acierto es de {f.pct(en(marcas[0]).acierto)}. La sequía de {camp(sequia.campania)} se vio
						temprano ({f.pct(sequia.deptos_en_rojo)} de los departamentos en rojo al {fl(sequia.fecha)}) porque fue muy fuerte.
					</li>
					<li><strong>Son {modelo.n_campanias} campañas y una sola sequía.</strong> No sabemos cómo responde en otras sequías.</li>
					<li>
						<strong>Lo parecido a lo normal no se juzga.</strong> Si el satélite ve una campaña a menos de {umbral}% de su historia, el mapa
						la muestra como normal y no cuenta como acierto ni como error.
					</li>
				{/if}
			</ul>
			<details>
				<summary>{L === 'en' ? 'Model error by campaign' : 'Error del modelo por campaña'}</summary>
				<table>
					<thead><tr>{#if L === 'en'}<th>Campaign</th><th>Model error</th><th>Historical-average error</th><th>Improvement</th>{:else}<th>Campaña</th><th>Error del modelo</th><th>Error del promedio histórico</th><th>Mejora</th>{/if}</tr></thead>
					<tbody>
						{#each por_campania as c (c.campania)}
							<tr><td>{c.campania}</td><td>{c.rmse_modelo} kg/ha</td><td>{c.rmse_base} kg/ha</td><td>{c.mejora > 0 ? '+' : ''}{f.dec(c.mejora)}%</td></tr>
						{/each}
					</tbody>
				</table>
				<p class="nota">{L === 'en' ? 'Root-mean-square error (RMSE) in kg/ha of the department yield estimate, validated leaving one campaign out at a time.' : 'Error medio cuadrático (RMSE) en kg/ha de la estimación de rinde del departamento, validado dejando una campaña afuera por vez.'}</p>
			</details>
		</div>
	</div>
</section>

<style>
	.alt {
		background: var(--surface-2);
		border-block: 1px solid var(--line);
	}
	.cabecera {
		display: grid;
		gap: 0.75rem;
		margin-bottom: 1.75rem;
	}
	.rejilla {
		display: grid;
		gap: 1rem;
	}
	@media (min-width: 1024px) {
		.rejilla {
			grid-template-columns: minmax(0, 1.6fr) minmax(280px, 1fr);
		}
	}
	.grafico {
		padding: 1.25rem;
		display: grid;
		gap: 0.6rem;
		align-content: start;
	}
	.sub {
		color: var(--ink-2);
		font-size: 0.9rem;
	}
	.datos {
		display: grid;
		gap: 1rem;
		align-content: start;
	}
	.dato {
		padding: 1rem 1.1rem;
		display: grid;
		grid-template-columns: auto 1fr;
		gap: 0.2rem 1rem;
		align-items: baseline;
	}
	.dato strong {
		font: 600 2.2rem / 1 var(--serif);
		color: var(--acento);
		min-width: 3.4ch;
	}
	.dato p {
		font-size: 0.9rem;
		color: var(--ink-2);
	}
	.honesto {
		margin-top: 1rem;
		padding: 1.25rem;
		display: grid;
		gap: 0.7rem;
	}
	.honesto ul {
		margin: 0;
		padding-left: 1.2rem;
		display: grid;
		gap: 0.5rem;
		color: var(--ink-2);
	}
	details {
		font-size: 0.88rem;
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
		padding: 0.3rem 0.5rem;
		text-align: left;
		border-bottom: 1px solid var(--line);
	}
	.nota {
		margin-top: 0.5rem;
		color: var(--muted);
		font-size: 0.8rem;
	}
</style>
