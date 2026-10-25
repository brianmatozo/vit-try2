<script lang="ts">
import { Button } from '@vitalcer/ui';
import { RefreshCw } from 'lucide-svelte';

interface Props {
	isFetching: boolean;
	onRefresh: () => void;
}

let { isFetching, onRefresh }: Props = $props();
</script>

<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
	<div>
		<h1 class="text-2xl font-bold tracking-tight text-gray-900">
			Ventas de Caja
		</h1>
		<p class="text-sm text-gray-500 mt-1">
			Registro y desglose de comprobantes cobrados en mostrador (POS).
		</p>
	</div>

	<div class="flex items-center gap-2">
		<Button
			variant="outline"
			onclick={onRefresh}
			disabled={isFetching}
			class="gap-1.5 cursor-pointer text-xs sm:text-sm"
		>
			<RefreshCw class="w-4 h-4 {isFetching ? 'animate-spin' : ''}" />
			<span>Actualizar</span>
		</Button>
	</div>
</div>
