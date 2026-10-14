<script lang="ts">
	import { onMount } from 'svelte';
	import { clasificar, COLOR, ETIQUETA, ICONO, veredicto, type Clase } from '../clases';
	import { monitor } from '../estado.svelte';
	import { anomaliaPct, fechaDecada, fechaLarga, mesCorto } from '../formato';
	import type { FeatureCollection } from 'geojson';
	import type { Monitor } from '../datos';
	import Mapa from './Mapa.svelte';
	import PanelDepto from './PanelDepto.svelte';

	let datos = $state<Monitor | null>(null);
	let geojson = $state<FeatureCollection | null>(null);
	let error = $state('');
	let tablaAbierta = $state(false);

	onMount(async () => {
		try {
			const [m, g] = await Promise.all([
				fetch('/data/monitor.json').then((r) => r.json() as Promise<Monitor>),
				fetch('/data/deptos.geojson').then((r) => r.json() as Promise<FeatureCollection>)
			]);
			datos = m;
			geojson = g;
			// Si el hero todavía no eligió una campaña, se arranca en la última, ya terminada.
			if (!monitor.campania) {
				monitor.campania = m.campanias[m.campanias.length - 1];
				monitor.decada = m.decadas.length - 1;
			}
		} catch {
			error = 'No se pudieron cargar los datos del mapa.';
		}
	});

	const n = $derived(datos?.decadas.length ?? 0);
	const fecha = $derived(datos && monitor.campania ? fechaDecada(monitor.campania, datos.decadas[monitor.decada] ?? datos.decadas[0]) : null);

	const clases = $derived.by(() => {
		const out: Record<string, { clase: Clase; an: number | null }> = {};
		if (!datos) return out;
		for (const [id, s] of Object.entries(datos.series[monitor.campania] ?? {})) {
			const an = s.an[monitor.decada] ?? null;
			out[id] = { clase: clasificar(an, s.np, datos.umbral, datos.min_puntos), an };
		}
		return out;
	});

	const resumen = $derived.by(() => {
		const cuenta: Record<Clase, number> = { mala: 0, normal: 0, buena: 0, pocos: 0, sin_dato: 0 };
		const anomalias: number[] = [];
		for (const c of Object.values(clases)) {
			cuenta[c.clase]++;
			if (c.an !== null && (c.clase === 'mala' || c.clase === 'normal' || c.clase === 'buena')) anomalias.push(c.an);
		}
		const evaluados = cuenta.mala + cuenta.normal + cuenta.buena;
		return { cuenta, evaluados, veredicto: datos ? veredicto(anomalias, datos.umbral) : null };
	});

	// Los que más se alejan de lo normal a esta fecha (para el panel vacío).
	const destacados = $derived(
		datos
			? Object.entries(clases)
					.filter(([, c]) => c.an !== null && (c.clase === 'mala' || c.clase === 'buena'))
					.sort((a, b) => Math.abs(b[1].an!) - Math.abs(a[1].an!))
					.slice(0, 5)
					.map(([id, c]) => ({ id, nombre: `${datos!.deptos[id].n} (${datos!.deptos[id].p})`, an: c.an!, clase: c.clase }))
			: []
	);

	const TITULO = {
		mala: 'Viene por debajo de lo normal',
		normal: 'Viene dentro de lo normal',
		buena: 'Viene por encima de lo normal'
	} as const;

	const opciones = $derived(datos ? Object.entries(datos.deptos).map(([id, d]) => ({ id, etiqueta: `${d.n} (${d.p})` })).sort((a, b) => a.etiqueta.localeCompare(b.etiqueta, 'es')) : []);
	const filasTabla = $derived(
		tablaAbierta && datos
			? Object.entries(clases).map(([id, c]) => ({ id, ...c, ...datos!.deptos[id] })).sort((a, b) => (a.an ?? 99) - (b.an ?? 99))
			: []
	);

	function buscar(e: Event) {
		const v = (e.currentTarget as HTMLInputElement).value;
		const o = opciones.find((x) => x.etiqueta === v);
		if (o) monitor.depto = o.id;
	}
	const elegir = (id: string) => (monitor.depto = id);

	function reproducir() {
		if (monitor.reproduciendo) monitor.reproduciendo = false;
		else {
			if (monitor.decada >= n - 1) monitor.decada = 0;
			monitor.reproduciendo = true;
		}
	}
	$effect(() => {
		if (!monitor.reproduciendo || !n) return;
		const t = setInterval(() => {
			if (monitor.decada >= n - 1) monitor.reproduciendo = false;
			else monitor.decada += 1;
		}, 550);
		return () => clearInterval(t);
	});
</script>

<section id="monitor" class="seccion">
	<div class="contenedor">
		<header class="cabecera">
			<p class="ojo">El monitor</p>
			<h2>Cómo viene cada departamento frente a su propia historia</h2>
			<p class="lede">
				Elegí una campaña y mové la fecha: cada departamento se pinta según su verdor acumulado contra el de otras campañas a esa misma fecha.
			</p>
		</header>

		{#if error}
			<p class="error" role="alert">{error}</p>
		{:else if datos && geojson && fecha}
			<div class="controles">
				<label>
					<span>Campaña</span>
					<select bind:value={monitor.campania} onchange={() => (monitor.reproduciendo = false)}>
						{#each [...datos.campanias].reverse() as c (c)}
							<option value={c}>{c}</option>
						{/each}
					</select>
				</label>
				<div class="tiempo">
					<button class="boton chico" onclick={reproducir} aria-pressed={monitor.reproduciendo}>
						{monitor.reproduciendo ? '❚❚ Pausar' : '▶ Reproducir'}
					</button>
					<label class="deslizador">
						<span>Al <strong>{fechaLarga(fecha, false)}</strong></span>
						<input type="range" min="0" max={n - 1} step="1" bind:value={monitor.decada} oninput={() => (monitor.reproduciendo = false)} />
						<span class="extremos" aria-hidden="true"><span>{mesCorto(fechaDecada(monitor.campania, datos.decadas[0]))}</span><span>{mesCorto(fechaDecada(monitor.campania, datos.decadas[n - 1]))}</span></span>
					</label>
				</div>
				<label class="buscar">
					<span>Departamento</span>
					<input list="deptos-lista" placeholder="Buscar, por ejemplo Pergamino" onchange={buscar} autocomplete="off" />
					<datalist id="deptos-lista">
						{#each opciones as o (o.id)}<option value={o.etiqueta}></option>{/each}
					</datalist>
				</label>
			</div>

			<div class="veredicto" aria-live="polite">
				{#if resumen.veredicto}
					<p class="titular"><span class="icono" aria-hidden="true">{ICONO[resumen.veredicto]}</span> {TITULO[resumen.veredicto]}</p>
				{/if}
				<p class="detalle">
					Al {fechaLarga(fecha)}: {resumen.cuenta.mala} de {resumen.evaluados} departamentos por debajo de lo normal, {resumen.cuenta.normal} normales y
					{resumen.cuenta.buena} por encima.
				</p>
			</div>

			<div class="rejilla">
				<div class="col-mapa">
					<Mapa {geojson} {clases} nombres={datos.deptos} seleccionado={monitor.depto} onelegir={elegir} />
					<div class="pie-mapa">
						<ul class="leyenda" aria-label="Leyenda del mapa">
							{#each ['mala', 'normal', 'buena', 'pocos'] as k (k)}
								<li>
									<span class="muestra" class:hachura={k === 'pocos'} style:background={k === 'pocos' ? undefined : COLOR[k as Clase]}></span>
									<span aria-hidden="true">{ICONO[k as Clase]}</span>
									{ETIQUETA[k as Clase]}{k === 'mala' || k === 'buena' ? ` (más de ${datos.umbral.toString().replace('.', ',')}%)` : ''}
								</li>
							{/each}
						</ul>
						{#if monitor.depto}
							<button class="boton secundario chico" onclick={() => (monitor.depto = null)}>Ver toda la región</button>
						{/if}
					</div>
				</div>
				<PanelDepto {datos} depto={monitor.depto} campania={monitor.campania} decada={monitor.decada} clase={monitor.depto ? clases[monitor.depto] : undefined} {destacados} onelegir={elegir} />
			</div>

			<details class="tabla" ontoggle={(e) => (tablaAbierta = (e.currentTarget as HTMLDetailsElement).open)}>
				<summary>Ver el mapa como tabla</summary>
				<div class="envoltura">
					<table>
						<thead><tr><th>Departamento</th><th>Provincia</th><th>Estado</th><th>Anomalía</th></tr></thead>
						<tbody>
							{#each filasTabla as f (f.id)}
								<tr>
									<td><button class="enlace" onclick={() => elegir(f.id)}>{f.n}</button></td>
									<td>{f.p}</td>
									<td>{ICONO[f.clase]} {ETIQUETA[f.clase]}</td>
									<td>{f.an !== null && f.clase !== 'pocos' ? anomaliaPct(f.an) : '–'}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</details>
		{:else}
			<div class="esqueleto" aria-busy="true">Cargando datos…</div>
		{/if}
	</div>
</section>

<style>
	.cabecera {
		display: grid;
		gap: 0.75rem;
		margin-bottom: 1.75rem;
	}
	.controles {
		display: grid;
		gap: 1rem 1.5rem;
		margin-bottom: 1.25rem;
		padding: 1rem 1.1rem;
		background: var(--surface);
		border: 1px solid var(--line);
		border-radius: var(--radio);
	}
	@media (min-width: 900px) {
		.controles {
			grid-template-columns: auto minmax(0, 1fr) minmax(0, 0.8fr);
			align-items: end;
		}
	}
	label {
		display: grid;
		gap: 0.3rem;
		font-size: 0.82rem;
		color: var(--muted);
	}
	label strong {
		color: var(--ink);
		font-size: 0.95rem;
	}
	select,
	input:not([type]) {
		padding: 0.5rem 0.65rem;
		border: 1px solid #c9c6bd;
		border-radius: 8px;
		background: #fff;
		color: var(--ink);
		min-width: 0;
	}
	.tiempo {
		display: flex;
		align-items: end;
		gap: 0.9rem;
	}
	.deslizador {
		flex: 1;
	}
	input[type='range'] {
		width: 100%;
		accent-color: var(--acento);
	}
	.extremos {
		display: flex;
		justify-content: space-between;
		font-size: 0.75rem;
		text-transform: capitalize;
	}
	.veredicto {
		margin-bottom: 1rem;
		display: grid;
		gap: 0.15rem;
	}
	.titular {
		font: 600 clamp(1.3rem, 2.6vw, 1.7rem) / 1.2 var(--serif);
	}
	.icono {
		display: inline-block;
		width: 1.5em;
	}
	.detalle {
		color: var(--ink-2);
	}
	.rejilla {
		display: grid;
		gap: 1rem;
		align-items: stretch;
	}
	@media (min-width: 1024px) {
		.rejilla {
			grid-template-columns: minmax(0, 1.55fr) minmax(320px, 1fr);
		}
	}
	.pie-mapa {
		display: flex;
		flex-wrap: wrap;
		justify-content: space-between;
		align-items: center;
		gap: 0.6rem 1rem;
		margin-top: 0.7rem;
	}
	.leyenda {
		display: flex;
		flex-wrap: wrap;
		gap: 0.3rem 1rem;
		margin: 0;
		padding: 0;
		list-style: none;
		font-size: 0.82rem;
		color: var(--ink-2);
	}
	.leyenda li {
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
	}
	.muestra {
		width: 14px;
		height: 14px;
		border-radius: 3px;
		border: 1px solid rgb(0 0 0 / 0.15);
	}
	.hachura {
		background: repeating-linear-gradient(135deg, #ece9e1 0 3px, #8f8a7e 3px 4px);
	}
	.tabla {
		margin-top: 1.5rem;
		font-size: 0.9rem;
	}
	.tabla summary {
		cursor: pointer;
		color: var(--acento);
	}
	.envoltura {
		max-height: 420px;
		overflow: auto;
		margin-top: 0.6rem;
		border: 1px solid var(--line);
		border-radius: var(--radio);
		background: var(--surface);
	}
	table {
		width: 100%;
		border-collapse: collapse;
		font-variant-numeric: tabular-nums;
	}
	th,
	td {
		padding: 0.4rem 0.7rem;
		text-align: left;
		border-bottom: 1px solid var(--line);
	}
	th {
		position: sticky;
		top: 0;
		background: #f3f1ea;
	}
	.enlace {
		appearance: none;
		border: 0;
		background: none;
		padding: 0;
		color: var(--acento);
		text-decoration: underline;
		cursor: pointer;
	}
	.esqueleto,
	.error {
		display: grid;
		place-items: center;
		min-height: 420px;
		color: var(--muted);
		background: var(--surface);
		border: 1px dashed var(--line);
		border-radius: var(--radio);
	}
	.error {
		color: var(--mala);
	}
</style>
