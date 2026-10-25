<script lang="ts">
import { Card } from '@vitalcer/ui';
import { Receipt } from 'lucide-svelte';

interface Props {
	hasAnyTickets: boolean;
	searchTerm: string;
}

let { hasAnyTickets, searchTerm }: Props = $props();
</script>

<Card class="p-12 text-center">
	<div class="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-3 text-gray-400">
		<Receipt class="w-6 h-6" />
	</div>
	{#if !hasAnyTickets}
		<div class="text-sm font-semibold text-gray-700">No hay ventas registradas aún</div>
		<p class="text-xs text-gray-400 max-w-sm mx-auto mt-1">
			Cuando realices cobros en la caja del POS, los comprobantes aparecerán automáticamente en este panel.
		</p>
	{:else}
		<div class="text-sm font-semibold text-gray-700">Sin coincidencias</div>
		<p class="text-xs text-gray-400 max-w-sm mx-auto mt-1">
			No se encontraron comprobantes que coincidan con "{searchTerm}".
		</p>
	{/if}
</Card>
