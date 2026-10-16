<script lang="ts">
	interface Lado {
		src: string;
		titulo: string;
		alt: string;
	}
	import { idioma } from '../i18n';

	let { antes, despues }: { antes: Lado; despues: Lado } = $props();
	const etiqueta = $derived(idioma() === 'en' ? 'Slide to compare the two dates' : 'Deslizá para comparar las dos fechas');
	let pos = $state(50);
</script>

<div class="marco" style:--pos="{pos}%">
	<img class="base" src={despues.src} alt={despues.alt} width="1600" height="1600" fetchpriority="high" />
	<img class="sup" src={antes.src} alt={antes.alt} width="1600" height="1600" fetchpriority="high" />
	<div class="linea" aria-hidden="true"><span class="perilla">◀ ▶</span></div>
	<span class="rotulo izq">{antes.titulo}</span>
	<span class="rotulo der">{despues.titulo}</span>
	<input type="range" min="0" max="100" step="1" bind:value={pos} aria-label={etiqueta} />
</div>

<style>
	.marco {
		position: relative;
		aspect-ratio: 1 / 1;
		width: 100%;
		overflow: hidden;
		border-radius: var(--radio);
		background: #2b2f2a;
		border: 1px solid var(--line);
		touch-action: pan-y;
	}
	img {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: cover;
		user-select: none;
		-webkit-user-drag: none;
	}
	.sup {
		clip-path: inset(0 calc(100% - var(--pos)) 0 0);
	}
	.linea {
		position: absolute;
		top: 0;
		bottom: 0;
		left: var(--pos);
		width: 2px;
		margin-left: -1px;
		background: #fff;
		box-shadow: 0 0 0 1px rgb(0 0 0 / 0.25);
		pointer-events: none;
	}
	.perilla {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		padding: 0.45rem 0.6rem;
		border-radius: 999px;
		background: #fff;
		color: var(--ink);
		font-size: 0.7rem;
		letter-spacing: 0.15em;
		box-shadow: 0 1px 6px rgb(0 0 0 / 0.35);
		white-space: nowrap;
	}
	.rotulo {
		position: absolute;
		bottom: 0.75rem;
		padding: 0.3rem 0.65rem;
		border-radius: 999px;
		background: rgb(20 24 20 / 0.78);
		color: #fff;
		font: 600 0.82rem/1.2 var(--sans);
		pointer-events: none;
	}
	.izq {
		left: 0.75rem;
	}
	.der {
		right: 0.75rem;
	}
	input {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		margin: 0;
		opacity: 0;
		cursor: ew-resize;
	}
	.marco:has(input:focus-visible) {
		outline: 3px solid var(--buena);
		outline-offset: 2px;
	}
</style>
