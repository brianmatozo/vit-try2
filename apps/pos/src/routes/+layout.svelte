<script lang="ts">
import './layout.css';
import { QueryClient, QueryClientProvider } from '@tanstack/svelte-query';
import { browser } from '$app/environment';
import favicon from '$lib/assets/favicon.svg';

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
