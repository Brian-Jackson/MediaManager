import { env } from '$env/dynamic/public';
import type { PageLoad } from './$types';

const apiUrl = env.PUBLIC_API_URL;

export const load: PageLoad = async ({ fetch }) => {
	const response = await fetch(apiUrl + '/auth/metadata', {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json'
		},
		credentials: 'include'
	});

	return { oauthProvider: await response.json() };
};
