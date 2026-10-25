<script lang="ts">
import { Button, Card, Input } from '@vitalcer/ui';
import { Search } from 'lucide-svelte';

interface Props {
	searchTerm: string;
	filteredCount: number;
	totalCount: number;
	onClearFilter: () => void;
}

let {
	searchTerm = $bindable(),
	filteredCount,
	totalCount,
	onClearFilter,
}: Props = $props();
</script>

<Card class="p-3 sm:p-4">
	<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
		<div class="relative flex-1 max-w-md">
			<Search class="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
			<Input
				bind:value={searchTerm}
				placeholder="Buscar por N° Ticket (POS-...), producto o PLU..."
				class="pl-9 h-10 text-sm"
			/>
		</div>

		<div class="text-xs text-gray-500 flex items-center justify-between sm:justify-end gap-3">
			<span>
				Mostrando <strong class="text-gray-900 font-semibold">{filteredCount}</strong> de {totalCount} comprobantes
			</span>
			{#if searchTerm}
				<Button
					variant="ghost"
					size="sm"
					onclick={onClearFilter}
					class="text-xs text-rose-600 hover:text-rose-700 h-8 px-2 cursor-pointer"
				>
					Limpiar filtro
				</Button>
			{/if}
		</div>
	</div>
</Card>
