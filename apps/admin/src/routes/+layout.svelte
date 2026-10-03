<script lang="ts">
import './layout.css';
import { QueryClient, QueryClientProvider } from '@tanstack/svelte-query';
import { client } from '@vitalcer/api';
import { browser } from '$app/environment';
import { page } from '$app/state';

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
			staleTime: 1000 * 60 * 2, // 2 minutes
			refetchOnWindowFocus: false,
		},
	},
});

const navLinks = [
	{ href: '/', label: 'Catálogo de Productos' },
	{ href: '/ledger', label: 'Auditoria' },
	{ href: '/actions', label: 'Acciones de Stock' },
];
</script>

<svelte:head>
  <title>Tablero de Control</title>
</svelte:head>

<QueryClientProvider client={queryClient}>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <!-- Minimal Clean Header -->
    <header class="bg-white border-b border-gray-200">
      <div class="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <div class="flex items-center gap-6">
          <span class="font-bold text-base tracking-tight text-gray-900">
            Vitalcer <span class="text-emerald-600 font-normal">Admin</span>
          </span>

          <nav class="flex items-center gap-1">
            {#each navLinks as link}
              {@const isActive = page.url.pathname === link.href}
              <a
                href={link.href}
                class="px-3 py-1.5 text-sm rounded-md transition-colors {isActive ? 'bg-gray-100 text-gray-900 font-medium' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'}"
              >
                {link.label}
              </a>
            {/each}
          </nav>
        </div>

        <div class="text-xs text-gray-400 font-mono">
          v1.0
        </div>
      </div>
    </header>

    <!-- Centered Content Area -->
    <main class="max-w-6xl w-full mx-auto px-4 py-6 flex-1 flex flex-col">
      {@render children()}
    </main>
  </div>
</QueryClientProvider>
