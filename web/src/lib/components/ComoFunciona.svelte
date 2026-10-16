<script lang="ts">
	import { idioma } from '../i18n';

	let { repo }: { repo: string } = $props();
	const T = {
		es: {
			ojo: 'El método',
			titulo: 'Cómo funciona',
			mas: 'El código, los tests y la metodología completa están en',
			repo: 'el repositorio',
			pasos: [
		{
			titulo: 'El satélite mira la soja, no todo el campo',
			texto: 'Sentinel-2 (programa Copernicus de la Agencia Espacial Europea) pasa cada 5 días. Usamos solo los píxeles que el INTA mapeó como soja ese año, para no mezclarla con maíz, monte o pasturas.'
		},
		{
			titulo: 'Una curva de verdor por departamento',
			texto: 'De esos píxeles sale un índice de vegetación (NDVI) cada 10 días, sin nubes y suavizado. Es una medida de cuánta soja verde hay y cuándo.'
		},
		{
			titulo: 'Se compara con su propia historia',
			texto: 'Cada fecha se contrasta con la misma fecha de las otras campañas del departamento. La diferencia es la anomalía: más de 5% por debajo, la campaña viene mal; más de 5% por encima, viene bien.'
		},
		{
			titulo: 'Se verifica contra los rindes oficiales',
			texto: 'Un modelo que suma lluvia y calor estima el rinde y se valida contra el MAGyP, siempre dejando afuera la campaña que se evalúa. Si no le gana al promedio histórico, el resultado se muestra igual.'
		}
			]
		},
		en: {
			ojo: 'The method',
			titulo: 'How it works',
			mas: 'The code, tests and full methodology are in',
			repo: 'the repository',
			pasos: [
		{
			titulo: 'The satellite looks at soybeans, not the whole field',
			texto: 'Sentinel-2 (the European Space Agency’s Copernicus programme) passes every 5 days. We use only the pixels INTA mapped as soybean that year, so it is not mixed up with maize, woodland or pasture.'
		},
		{
			titulo: 'One greenness curve per department',
			texto: 'From those pixels we get a vegetation index (NDVI) every 10 days, cloud-free and smoothed. It measures how much green soybean there is and when.'
		},
		{
			titulo: 'Compared with its own history',
			texto: 'Each date is set against the same date in the department’s other campaigns. The difference is the anomaly: more than 5% below, the campaign is going badly; more than 5% above, it is going well.'
		},
		{
			titulo: 'Checked against official yields',
			texto: 'A model that adds rainfall and heat estimates yield and is validated against MAGyP, always leaving out the campaign being evaluated. If it does not beat the historical average, the result is shown anyway.'
		}
			]
		}
	};
	const t = $derived(T[idioma()]);
</script>

<section id="como" class="seccion">
	<div class="contenedor">
		<header class="cabecera">
			<p class="ojo">{t.ojo}</p>
			<h2>{t.titulo}</h2>
		</header>
		<ol class="pasos">
			{#each t.pasos as p, i (p.titulo)}
				<li class="tarjeta">
					<span class="numero" aria-hidden="true">{i + 1}</span>
					<h3>{p.titulo}</h3>
					<p>{p.texto}</p>
				</li>
			{/each}
		</ol>
		<p class="mas">
			{t.mas} <a href={repo}>{t.repo}</a>.
		</p>
	</div>
</section>

<style>
	.cabecera {
		margin-bottom: 1.5rem;
		display: grid;
		gap: 0.75rem;
	}
	.pasos {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		gap: 1rem;
	}
	@media (min-width: 720px) {
		.pasos {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}
	@media (min-width: 1100px) {
		.pasos {
			grid-template-columns: repeat(4, minmax(0, 1fr));
		}
	}
	li {
		padding: 1.25rem;
		display: grid;
		gap: 0.6rem;
		align-content: start;
	}
	.numero {
		display: grid;
		place-items: center;
		width: 2rem;
		height: 2rem;
		border-radius: 50%;
		background: var(--acento-claro);
		color: var(--acento);
		font-weight: 700;
	}
	li p {
		color: var(--ink-2);
		font-size: 0.93rem;
	}
	.mas {
		margin-top: 1.5rem;
		color: var(--ink-2);
	}
</style>
