<script lang="ts">
	import '../app.css';
	import ComoFunciona from '../lib/components/ComoFunciona.svelte';
	import Funciona from '../lib/components/Funciona.svelte';
	import Hero from '../lib/components/Hero.svelte';
	import Monitor from '../lib/components/Monitor.svelte';
	import hero from '../lib/data/hero_imagenes.json';
	import validacion from '../lib/data/validacion.json';
	import type { HeroImagenes, Validacion } from '../lib/datos';

	const REPO = 'https://github.com/datakrdo/agro-monitor-pampa';
	// og:image tiene que ser una URL absoluta: se completa con la del deploy (https://<proyecto>.pages.dev).
	const REPO_SITIO = 'https://agro-monitor-pampa.pages.dev';
	const v = validacion as Validacion;
	const decadas = v.acierto.map((a) => a.fecha);
	const titulo = '¿Viene buena o mala la campaña de soja? · Agro Monitor Pampa';
	const descripcion = 'Un satélite mide el verdor de la soja en cada departamento de la pampa húmeda y lo compara con su historia para anticipar si la campaña viene buena o mala.';
</script>

<svelte:head>
	<title>{titulo}</title>
	<meta name="description" content={descripcion} />
	<meta property="og:title" content={titulo} />
	<meta property="og:description" content={descripcion} />
	<meta property="og:type" content="website" />
	<meta property="og:locale" content="es_AR" />
	<meta property="og:image" content="{REPO_SITIO}/img/og.png" />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />
	<meta name="twitter:card" content="summary_large_image" />
</svelte:head>

<header class="barra">
	<div class="contenedor barra-in">
		<a class="marca" href="#top">🌱 Agro Monitor Pampa</a>
		<nav aria-label="Secciones">
			<a href="#monitor">Monitor</a>
			<a href="#funciona">¿Cuánto acierta?</a>
			<a href="#como">Cómo funciona</a>
			<a href={REPO}>Código</a>
		</nav>
	</div>
</header>

<main id="top">
	<Hero validacion={v} imagenes={hero as HeroImagenes} {decadas} />
	<Monitor />
	<Funciona validacion={v} />
	<ComoFunciona repo={REPO} />
</main>

<footer class="pie">
	<div class="contenedor">
		<p>
			<strong>Fuentes.</strong> Imágenes Sentinel-2 L2A (Copernicus Data Space, ESA) · máscara de cultivos: Mapa Nacional de Cultivos, INTA · rendimientos: estimaciones agrícolas, MAGyP ·
			clima: reanálisis ERA5 vía Open-Meteo · mapa base: OpenFreeMap, © OpenMapTiles, datos de OpenStreetMap.
		</p>
		<p>Proyecto de portfolio. Datos generados el {v.generado}. Los rindes y las campañas son los publicados por las fuentes; las estimaciones son de este proyecto y no una recomendación comercial.</p>
	</div>
</footer>

<style>
	.barra {
		position: sticky;
		top: 0;
		z-index: 10;
		background: rgb(250 249 246 / 0.92);
		backdrop-filter: blur(8px);
		border-bottom: 1px solid var(--line);
	}
	.barra-in {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		min-height: 3.4rem;
	}
	.marca {
		font: 600 1.05rem var(--serif);
		color: var(--ink);
		text-decoration: none;
		white-space: nowrap;
	}
	nav {
		display: flex;
		gap: 1.2rem;
		font-size: 0.92rem;
		overflow-x: auto;
	}
	nav a {
		color: var(--ink-2);
		text-decoration: none;
		white-space: nowrap;
	}
	nav a:hover {
		color: var(--acento);
		text-decoration: underline;
	}
	@media (max-width: 640px) {
		nav a:not(:first-child):not(:last-child) {
			display: none;
		}
	}
	.pie {
		padding: 2rem 0 3rem;
		border-top: 1px solid var(--line);
		background: #f3f1ea;
		color: var(--muted);
		font-size: 0.85rem;
	}
	.pie .contenedor {
		display: grid;
		gap: 0.6rem;
	}
	.pie strong {
		color: var(--ink-2);
	}
</style>
