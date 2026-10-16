import type { Handle } from '@sveltejs/kit/hooks';

export const handle: Handle = ({ event, resolve }) => {
	const lang = event.url.pathname.startsWith('/en') ? 'en' : 'es';
	return resolve(event, { transformPageChunk: ({ html }) => html.replace('%lang%', lang) });
};
