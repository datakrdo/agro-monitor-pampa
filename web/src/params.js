import { defineParams } from '@sveltejs/kit/params';

export const params = defineParams({
	en: (/** @type {string} */ param) => (param === 'en' ? param : undefined)
});
