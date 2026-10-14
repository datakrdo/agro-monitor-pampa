// Estado compartido entre el hero (que abre el monitor en la sequía) y el monitor.
export const monitor = $state({
	campania: '',
	decada: 0,
	depto: null as string | null,
	reproduciendo: false
});
