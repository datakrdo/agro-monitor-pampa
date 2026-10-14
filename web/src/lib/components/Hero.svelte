<script lang="ts">
	import { monitor } from '../estado.svelte';
	import { fechaDecada, fechaLarga, kgha, pct } from '../formato';
	import type { HeroImagenes, Validacion } from '../datos';
	import AntesDespues from './AntesDespues.svelte';

	let { validacion, imagenes, decadas }: { validacion: Validacion; imagenes: HeroImagenes; decadas: string[] } = $props();

	const sequia = $derived(validacion.sequia);
	const hero = $derived(validacion.hero);
	const mala = $derived(imagenes.imagenes[0]);
	const normal = $derived(imagenes.imagenes[1]);
	const mes = (iso: string) => fechaLarga(new Date(iso + 'T00:00:00Z'), false).split(' de ')[1];
	const rango = (i: HeroImagenes['imagenes'][number]) =>
		`${fechaLarga(new Date(i.desde + 'T00:00:00Z'), false)} al ${fechaLarga(new Date(i.hasta + 'T00:00:00Z'), false)} de ${i.anio}`;

	function verSequia() {
		const quieto = matchMedia('(prefers-reduced-motion: reduce)').matches;
		monitor.campania = sequia.campania;
		monitor.depto = null;
		// Con movimiento reducido no se anima: se deja en la fecha del dato.
		monitor.decada = quieto ? decadas.indexOf(sequia.fecha) : 0;
		monitor.reproduciendo = !quieto;
		document.getElementById('monitor')?.scrollIntoView({ behavior: quieto ? 'auto' : 'smooth' });
	}
</script>

<section class="hero">
	<div class="contenedor rejilla">
		<div class="texto">
			<p class="ojo">Soja · Pampa húmeda · Sentinel-2</p>
			<h1>¿Viene buena o mala la campaña de soja?</h1>
			<p class="lede">
				Un satélite mide cuánto verde tiene la soja de cada departamento y lo compara con su propia historia. Cuando una campaña viene más
				pobre que otras, se nota meses antes de la cosecha.
			</p>
			<p class="dato">
				<strong>{pct(sequia.deptos_en_rojo)}</strong>
				<span>
					de los departamentos ya estaba por debajo de lo normal el {fechaLarga(fechaDecada(sequia.campania, sequia.fecha))}. La campaña
					{sequia.campania.replace('/20', '/')} cerró con rindes {pct(Math.abs(sequia.desvio_medio))} por debajo del promedio de cada
					departamento.
				</span>
			</p>
			<div class="acciones">
				<button class="boton" onclick={verSequia}>Ver cómo se vio la sequía</button>
				<a class="boton secundario" href="#funciona">¿Cuánto acierta?</a>
			</div>
		</div>
		<figure class="imagen">
			<AntesDespues
				antes={{
					src: mala.archivo,
					titulo: `${mes(mala.centro)} ${mala.anio} · sequía`,
					alt: `Imagen satelital de campos de ${hero.depto} en ${mes(mala.centro)} de ${mala.anio}, con lotes de soja secos y pardos.`
				}}
				despues={{
					src: normal.archivo,
					titulo: `${mes(normal.centro)} ${normal.anio}`,
					alt: `Los mismos campos de ${hero.depto} en ${mes(normal.centro)} de ${normal.anio}, con la soja verde y densa.`
				}}
			/>
			<figcaption>
				<strong>{hero.depto}, {hero.provincia}.</strong> Color real de Sentinel-2, mediana de ~30 días ({rango(mala)}, izquierda; {rango(normal)}, derecha).
				Rinde oficial: {kgha(hero.rinde_mala)} en {hero.campania_mala.replace('/20', '/')} contra {kgha(hero.rinde_normal)} en {hero.campania_normal.replace('/20', '/')}.
			</figcaption>
		</figure>
	</div>
</section>

<style>
	.hero {
		padding: clamp(2rem, 5vw, 4rem) 0 clamp(2.5rem, 6vw, 4.5rem);
		background: linear-gradient(180deg, #f3f1ea 0%, var(--bg) 100%);
		border-bottom: 1px solid var(--line);
	}
	.rejilla {
		display: grid;
		gap: clamp(1.5rem, 4vw, 3.5rem);
		align-items: center;
	}
	@media (min-width: 960px) {
		.rejilla {
			grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
		}
	}
	.texto {
		display: grid;
		gap: 1.25rem;
	}
	.dato {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: 0.2rem 1rem;
		align-items: baseline;
		padding: 1rem 1.1rem;
		background: var(--surface);
		border: 1px solid var(--line);
		border-left: 4px solid var(--mala);
		border-radius: var(--radio);
		max-width: 62ch;
	}
	.dato strong {
		font: 600 clamp(2.4rem, 5vw, 3.2rem) / 1 var(--serif);
		letter-spacing: -0.02em;
	}
	.dato span {
		color: var(--ink-2);
		font-size: 0.98rem;
	}
	.acciones {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
	}
	.imagen {
		margin: 0;
		display: grid;
		gap: 0.7rem;
	}
	figcaption {
		font-size: 0.82rem;
		color: var(--muted);
		line-height: 1.5;
	}
	figcaption strong {
		color: var(--ink-2);
	}
</style>
