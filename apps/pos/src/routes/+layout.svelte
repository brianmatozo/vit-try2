<script lang="ts">
import './layout.css';
import { QueryClient, QueryClientProvider } from '@tanstack/svelte-query';
import { client } from '@vitalcer/api';
import { browser } from '$app/environment';
import favicon from '$lib/assets/favicon.svg';

if (browser) {
	client.setConfig({
		baseUrl: import.meta.env.VITE_API_URL || '',
	});
}

let { children } = $props();

const queryClient = new QueryClient({
	defaultOptions: {
		queries: {
			enabled: browser,
			staleTime: 1000 * 60 * 5,
		},
	},
});
</script>

<svelte:head>
	<title>Vitalcer POS</title>
	<link rel="icon" href={favicon} />
</svelte:head>

<QueryClientProvider client={queryClient}>
	{@render children()}
</QueryClientProvider>
