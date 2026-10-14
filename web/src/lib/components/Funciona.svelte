<script lang="ts">
	import * as Plot from '@observablehq/plot';
	import { fechaDecada, fechaLarga, mesCorto, pct } from '../formato';
	import type { Validacion } from '../datos';

	let { validacion }: { validacion: Validacion } = $props();
	const acierto = $derived(validacion.acierto);
	const modelo = $derived(validacion.modelo);
	const sequia = $derived(validacion.sequia);
	const por_campania = $derived(validacion.por_campania);
	const en = (mmdd: string) => acierto.find((a) => a.fecha === mmdd)!;
	// El año es solo de referencia para ubicar nov-may en el eje.
	const REF = '2022/2023';
	const marcas = ['12-01', '01-01', '03-01'];
	let ancho = $state(640);
	let host: HTMLDivElement;

	$effect(() => {
		const filas = acierto.map((a) => ({ ...a, f: fechaDecada(REF, a.fecha) }));
		const g = Plot.plot({
			width: ancho, height: Math.max(300, Math.min(380, ancho * 0.52)), marginLeft: 44, marginRight: ancho > 520 ? 118 : 12, marginTop: 24,
			style: { background: 'transparent', fontSize: '12px', fontFamily: 'inherit', color: '#646c75', overflow: 'visible' },
			x: { type: 'utc', label: null, ticks: 'month', tickFormat: (d: Date) => mesCorto(d) },
			y: { domain: [0.4, 0.9], label: null, grid: true, ticks: 5, tickFormat: (d: number) => `${Math.round(d * 100)}%` },
			marks: [
				Plot.ruleY([0.5], { stroke: '#8a9099', strokeDasharray: '4 3' }),
				Plot.text([{ f: filas[0].f }], { x: 'f', y: 0.5, text: () => 'Tirar una moneda: 50%', dy: 11, textAnchor: 'start', fill: '#646c75' }),
				Plot.lineY(filas, { x: 'f', y: 'acierto_sin_umbral', stroke: '#8a9099', strokeWidth: 2 }),
				Plot.lineY(filas, { x: 'f', y: 'acierto', stroke: '#1f5f3a', strokeWidth: 3 }),
				ancho > 520 ? Plot.text(filas.slice(-1), { x: 'f', y: 'acierto', text: () => 'Con señal clara', dx: 8, textAnchor: 'start', fill: '#1f5f3a', fontWeight: 600 }) : null,
				ancho > 520 ? Plot.text(filas.slice(-1), { x: 'f', y: 'acierto_sin_umbral', text: () => 'Todos los casos', dx: 8, dy: 4, textAnchor: 'start', fill: '#646c75' }) : null,
				Plot.dot(filas.filter((r) => marcas.includes(r.fecha)), { x: 'f', y: 'acierto', r: 5, fill: '#1f5f3a', stroke: '#fff', strokeWidth: 2 }),
				Plot.text(filas.filter((r) => marcas.includes(r.fecha)), { x: 'f', y: 'acierto', text: (r: { acierto: number }) => pct(r.acierto), dy: -14, fontWeight: 700, fill: '#1b1f23' }),
				Plot.tip(filas, Plot.pointerX({
					x: 'f', y: 'acierto',
					title: (r: (typeof filas)[number]) => `Al ${fechaLarga(r.f, false)}\nCon señal clara: ${pct(r.acierto)}\nTodos los casos: ${pct(r.acierto_sin_umbral)}\nCasos con señal clara: ${pct(r.marcados)}`
				}))
			]
		});
		host.replaceChildren(g);
	});
</script>

<section id="funciona" class="seccion alt">
	<div class="contenedor">
		<header class="cabecera">
			<p class="ojo">La validación</p>
			<h2>¿Cuánto acierta?</h2>
			<p class="lede">
				Probamos el método con los rindes oficiales del MAGyP: {modelo.n_campanias} campañas ({validacion.por_campania[0].campania.replace('/20', '/')} a
				{validacion.por_campania.at(-1)?.campania.replace('/20', '/')}) y {modelo.n_deptos} departamentos. Cada campaña se evalúa sin que el método haya visto
				sus resultados.
			</p>
		</header>

		<div class="rejilla">
			<div class="tarjeta grafico">
				<h3>Cuanto más avanza la campaña, más acierta</h3>
				<p class="sub">
					Porcentaje de casos en que el satélite acertó si la campaña terminó por encima o por debajo de lo normal de cada departamento.
				</p>
				<div bind:this={host} bind:clientWidth={ancho} role="img" aria-label="Línea de acierto según la fecha, de {pct(en('12-01').acierto)} el 1 de diciembre a {pct(acierto.at(-1)!.acierto)} al cierre"></div>
				<details>
					<summary>Ver los datos como tabla</summary>
					<table>
						<thead><tr><th>Al</th><th>Con señal clara</th><th>Todos los casos</th><th>Casos con señal clara</th></tr></thead>
						<tbody>
							{#each acierto as a (a.fecha)}
								<tr>
									<td>{fechaLarga(fechaDecada(REF, a.fecha), false)}</td><td>{pct(a.acierto)}</td><td>{pct(a.acierto_sin_umbral)}</td><td>{pct(a.marcados)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</details>
			</div>

			<div class="datos">
				<div class="tarjeta dato">
					<strong>{pct(en('03-01').acierto)}</strong>
					<p>
						acierta al 1 de marzo, cuando la anomalía es clara (más de {validacion.umbral.toString().replace('.', ',')}% hacia un lado: {pct(en('03-01').marcados)} de los casos).
					</p>
				</div>
				<div class="tarjeta dato">
					<strong>{pct(modelo.precision_mala)}</strong>
					<p>
						de las veces que el modelo anticipa un rinde más de 10% por debajo de lo normal, acierta ({modelo.n_mala} casos). Solo {pct(modelo.mala_era_buena)} terminó por
						encima.
					</p>
				</div>
				<div class="tarjeta dato">
					<strong>{Math.round(modelo.mejora)}%</strong>
					<p>
						menos error que usar el promedio histórico de cada departamento. Sin la sequía de {sequia.campania.replace('/20', '/')}, la mejora es de
						{Math.round(modelo.mejora_sin_peor)}%.
					</p>
				</div>
			</div>
		</div>

		<div class="tarjeta honesto">
			<h3>Lo que hay que saber</h3>
			<ul>
				<li>
					<strong>Al principio es difícil.</strong> El 1 de diciembre el acierto es de {pct(en('12-01').acierto)}, cerca de tirar una moneda. La sequía de {sequia.campania.replace('/20', '/')} se vio
					temprano ({pct(sequia.deptos_en_rojo)} de los departamentos en rojo ese día) porque fue muy fuerte.
				</li>
				<li><strong>Son {modelo.n_campanias} campañas y una sola sequía.</strong> No sabemos cómo responde en otras sequías.</li>
				<li>
					<strong>Lo parecido a lo normal no se juzga.</strong> Si el satélite ve una campaña a menos de {validacion.umbral.toString().replace('.', ',')}% de su historia, el mapa
					la muestra como normal y no cuenta como acierto ni como error.
				</li>
			</ul>
			<details>
				<summary>Error del modelo por campaña</summary>
				<table>
					<thead><tr><th>Campaña</th><th>Error del modelo</th><th>Error del promedio histórico</th><th>Mejora</th></tr></thead>
					<tbody>
						{#each por_campania as c (c.campania)}
							<tr><td>{c.campania}</td><td>{c.rmse_modelo} kg/ha</td><td>{c.rmse_base} kg/ha</td><td>{c.mejora > 0 ? '+' : ''}{c.mejora.toString().replace('.', ',')}%</td></tr>
						{/each}
					</tbody>
				</table>
				<p class="nota">Error medio cuadrático (RMSE) en kg/ha de la estimación de rinde del departamento, validado dejando una campaña afuera por vez.</p>
			</details>
		</div>
	</div>
</section>

<style>
	.alt {
		background: #f3f1ea;
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
