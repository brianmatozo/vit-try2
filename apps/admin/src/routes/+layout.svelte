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
			staleTime: 1000 * 60 * 5, // 5 minutes cache
			refetchOnWindowFocus: false,
		},
	},
});

const navLinks = [
	{ href: '/', label: 'Catálogo de Productos', shortLabel: 'Catálogo' },
	{ href: '/ledger', label: 'Auditoría', shortLabel: 'Auditoría' },
	{ href: '/actions', label: 'Acciones de Stock', shortLabel: 'Operaciones' },
];
</script>

<svelte:head>
  <title>Tablero de Control</title>
</svelte:head>

<QueryClientProvider client={queryClient}>
  <div class="min-h-screen bg-gray-50 flex flex-col w-full overflow-x-hidden">
    <!-- Responsive Header with Horizontal Scrolling Nav for Small Screens -->
    <header class="bg-white border-b border-gray-200 sticky top-0 z-30">
      <div class="max-w-6xl mx-auto px-3 sm:px-4">
        <div class="h-14 flex items-center justify-between gap-2 sm:gap-6">
          <a href="/" class="flex items-center gap-1.5 shrink-0 select-none">
            <span class="font-bold text-base tracking-tight text-gray-900">
              Vitalcer <span class="text-emerald-600 font-normal">Admin</span>
            </span>
          </a>

          <nav class="flex items-center gap-1 overflow-x-auto no-scrollbar py-1">
            {#each navLinks as link}
              {@const isActive = page.url.pathname === link.href}
              <a
                href={link.href}
                class="px-2.5 sm:px-3 py-1.5 text-xs sm:text-sm rounded-md transition-colors whitespace-nowrap shrink-0 {isActive ? 'bg-gray-100 text-gray-900 font-semibold' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50 font-medium'}"
              >
                <span class="sm:hidden">{link.shortLabel}</span>
                <span class="hidden sm:inline">{link.label}</span>
              </a>
            {/each}
          </nav>

          <div class="hidden md:block text-xs text-gray-400 font-mono shrink-0">
            v1.0
          </div>
        </div>
      </div>
    </header>

    <!-- Centered Responsive Content Area -->
    <main class="max-w-6xl w-full mx-auto px-3 sm:px-4 py-4 sm:py-6 flex-1 flex flex-col min-w-0">
      {@render children()}
    </main>
  </div>
</QueryClientProvider>
