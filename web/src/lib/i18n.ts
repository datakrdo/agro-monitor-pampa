import { page } from '$app/state';

export type Idioma = 'es' | 'en';

/** Idioma de la URL: `/en` es inglés, el resto castellano. */
export const idioma = (): Idioma => (page.params.lang === 'en' ? 'en' : 'es');
