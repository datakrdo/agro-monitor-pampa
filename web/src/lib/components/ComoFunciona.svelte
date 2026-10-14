<script lang="ts">
	let { repo }: { repo: string } = $props();
	const pasos = [
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
	];
</script>

<section id="como" class="seccion">
	<div class="contenedor">
		<header class="cabecera">
			<p class="ojo">El método</p>
			<h2>Cómo funciona</h2>
		</header>
		<ol class="pasos">
			{#each pasos as p, i (p.titulo)}
				<li class="tarjeta">
					<span class="numero" aria-hidden="true">{i + 1}</span>
					<h3>{p.titulo}</h3>
					<p>{p.texto}</p>
				</li>
			{/each}
		</ol>
		<p class="mas">
			El código, los tests y la metodología completa están en <a href={repo}>el repositorio</a>.
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
