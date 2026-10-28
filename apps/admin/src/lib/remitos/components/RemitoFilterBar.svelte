<script lang="ts">
import { Input } from '@vitalcer/ui';
import { Search, X } from 'lucide-svelte';
import type { RemitoTab } from '../remitos-state.svelte';

interface Props {
	searchTerm: string;
	activeTab: RemitoTab;
	stagedCount: number;
	committedCount: number;
	totalCount: number;
	onTabChange: (tab: RemitoTab) => void;
	onClear: () => void;
}

let {
	searchTerm = $bindable(''),
	activeTab,
	stagedCount,
	committedCount,
	totalCount,
	onTabChange,
	onClear,
}: Props = $props();
</script>

<div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
	<!-- Tab Switcher -->
	<div class="inline-flex p-1 bg-gray-100 rounded-lg text-xs font-medium self-start sm:self-auto">
		<button
			type="button"
			onclick={() => onTabChange('staged')}
			class="px-3 py-1.5 rounded-md transition-all flex items-center gap-1.5 {activeTab === 'staged' ? 'bg-white text-gray-900 font-semibold shadow-xs' : 'text-gray-500 hover:text-gray-900'}"
		>
			<span>Pendientes</span>
			{#if stagedCount > 0}
				<span class="px-1.5 py-0.2 rounded-full text-2xs font-bold bg-amber-100 text-amber-800">
					{stagedCount}
				</span>
			{/if}
		</button>

		<button
			type="button"
			onclick={() => onTabChange('committed')}
			class="px-3 py-1.5 rounded-md transition-all flex items-center gap-1.5 {activeTab === 'committed' ? 'bg-white text-gray-900 font-semibold shadow-xs' : 'text-gray-500 hover:text-gray-900'}"
		>
			<span>Confirmados</span>
			{#if committedCount > 0}
				<span class="px-1.5 py-0.2 rounded-full text-2xs font-semibold bg-emerald-100 text-emerald-800">
					{committedCount}
				</span>
			{/if}
		</button>

		<button
			type="button"
			onclick={() => onTabChange('all')}
			class="px-3 py-1.5 rounded-md transition-all {activeTab === 'all' ? 'bg-white text-gray-900 font-semibold shadow-xs' : 'text-gray-500 hover:text-gray-900'}"
		>
			Todos ({totalCount})
		</button>
	</div>

	<!-- Search Input -->
	<div class="relative w-full sm:w-72">
		<Search class="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
		<Input
			placeholder="Buscar por distribuidor o número..."
			bind:value={searchTerm}
			class="pl-9 pr-8 text-xs"
		/>
		{#if searchTerm}
			<button
				type="button"
				onclick={onClear}
				class="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-0.5"
			>
				<X class="w-3.5 h-3.5" />
			</button>
		{/if}
	</div>
</div>
