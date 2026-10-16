<script lang="ts">
	import '../../app.css';
	import ComoFunciona from '../../lib/components/ComoFunciona.svelte';
	import Funciona from '../../lib/components/Funciona.svelte';
	import Hero from '../../lib/components/Hero.svelte';
	import Monitor from '../../lib/components/Monitor.svelte';
	import hero from '../../lib/data/hero_imagenes.json';
	import validacion from '../../lib/data/validacion.json';
	import type { HeroImagenes, Validacion } from '../../lib/datos';
	import { idioma } from '../../lib/i18n';

	const REPO = 'https://github.com/datakrdo/agro-monitor-pampa';
	// og:image tiene que ser una URL absoluta: se completa con la del deploy (https://<proyecto>.pages.dev).
	const REPO_SITIO = 'https://agro-monitor-pampa.pages.dev';
	const v = validacion as Validacion;
	const decadas = v.acierto.map((a) => a.fecha);
	const L = $derived(idioma());
	const T = {
		es: {
			titulo: '¿Viene buena o mala la campaña de soja? · Agro Monitor Pampa',
			descripcion: 'Un satélite mide el verdor de la soja en cada departamento de la pampa húmeda y lo compara con su historia para anticipar si la campaña viene buena o mala.',
			locale: 'es_AR', nav: ['Monitor', '¿Cuánto acierta?', 'Cómo funciona', 'Código'], secciones: 'Secciones', idioma: 'Idioma',
			fuentes: 'Fuentes.',
			fuentesTexto: 'Imágenes Sentinel-2 L2A (Copernicus Data Space, ESA) · máscara de cultivos: Mapa Nacional de Cultivos, INTA · rendimientos: estimaciones agrícolas, MAGyP · clima: reanálisis ERA5 vía Open-Meteo · mapa base: OpenFreeMap, © OpenMapTiles, datos de OpenStreetMap.',
			pie: (g: string) => `Proyecto de portfolio. Datos generados el ${g}. Los rindes y las campañas son los publicados por las fuentes; las estimaciones son de este proyecto y no una recomendación comercial.`
		},
		en: {
			titulo: 'Is this soybean campaign going well or badly? · Agro Monitor Pampa',
			descripcion: 'A satellite measures how green the soybeans are in each department of the humid Pampas and compares it with its history to anticipate whether the campaign is going well or badly.',
			locale: 'en_US', nav: ['Monitor', 'How accurate is it?', 'How it works', 'Code'], secciones: 'Sections', idioma: 'Language',
			fuentes: 'Sources.',
			fuentesTexto: 'Sentinel-2 L2A imagery (Copernicus Data Space, ESA) · crop mask: National Crop Map (Mapa Nacional de Cultivos), INTA · yields: agricultural estimates, MAGyP · weather: ERA5 reanalysis via Open-Meteo · basemap: OpenFreeMap, © OpenMapTiles, OpenStreetMap data.',
			pie: (g: string) => `Portfolio project. Data generated on ${g}. Yields and campaigns are as published by the sources; the estimates are this project’s own and not commercial advice.`
		}
	};
	const t = $derived(T[L]);
	// El servidor fija <html lang>; al cambiar de idioma sin recargar hay que seguirlo a mano.
	$effect(() => {
		document.documentElement.lang = L;
	});
</script>

<svelte:head>
	<title>{t.titulo}</title>
	<meta name="description" content={t.descripcion} />
	<meta property="og:title" content={t.titulo} />
	<meta property="og:description" content={t.descripcion} />
	<meta property="og:type" content="website" />
	<meta property="og:locale" content={t.locale} />
	<meta property="og:image" content="{REPO_SITIO}/img/og.png" />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />
	<meta name="twitter:card" content="summary_large_image" />
	<link rel="canonical" href={L === 'en' ? `${REPO_SITIO}/en/` : `${REPO_SITIO}/`} />
	<link rel="alternate" hreflang="es" href="{REPO_SITIO}/" />
	<link rel="alternate" hreflang="en" href="{REPO_SITIO}/en/" />
	<link rel="alternate" hreflang="x-default" href="{REPO_SITIO}/" />
</svelte:head>

<header class="barra">
	<div class="contenedor barra-in">
		<a class="marca" href="#top">🌱 Agro Monitor Pampa</a>
		<nav aria-label={t.secciones}>
			<a href="#monitor">{t.nav[0]}</a>
			<a href="#funciona">{t.nav[1]}</a>
			<a href="#como">{t.nav[2]}</a>
			<a href={REPO}>{t.nav[3]}</a>
		</nav>
		<div class="idioma" role="group" aria-label={t.idioma}>
			<a href="/" hreflang="es" lang="es" aria-current={L === 'es' ? 'true' : undefined}>ES</a>
			<a href="/en/" hreflang="en" lang="en" aria-current={L === 'en' ? 'true' : undefined}>EN</a>
		</div>
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
			<strong>{t.fuentes}</strong> {t.fuentesTexto}
		</p>
		<p>{t.pie(v.generado)}</p>
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
	.idioma {
		display: flex;
		border: 1px solid var(--line);
		border-radius: 999px;
		overflow: hidden;
		font-size: 0.82rem;
		font-weight: 600;
		flex: none;
	}
	.idioma a {
		padding: 0.25rem 0.65rem;
		color: var(--ink-2);
		text-decoration: none;
	}
	.idioma a[aria-current='true'] {
		background: var(--ink);
		color: #fff;
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
