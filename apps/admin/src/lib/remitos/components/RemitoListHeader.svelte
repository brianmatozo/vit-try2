<script lang="ts">
import { Button } from '@vitalcer/ui';
import { Plus, RefreshCw, Settings, Sparkles } from 'lucide-svelte';
import type { RemitoConfigState } from '../remito-config-state.svelte';

interface Props {
	config: RemitoConfigState;
	isFetching: boolean;
	onRefresh: () => void;
}

let { config, isFetching, onRefresh }: Props = $props();
</script>

<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-2 border-b border-gray-200">
	<div>
		<h1 class="text-xl sm:text-2xl font-bold tracking-tight text-gray-900 flex items-center gap-2">
			Remitos & Recepción
			<span class="inline-flex items-center gap-1 text-2xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
				<Sparkles class="w-3 h-3 text-emerald-600" />
				Vision AI
			</span>
		</h1>
		<p class="text-xs text-gray-500 mt-0.5">
			Ingreso automatizado de stock y cálculo de costos con split fiscal blanco/negro
		</p>
	</div>

	<div class="flex items-center gap-2">
		<Button
			variant="outline"
			size="sm"
			onclick={() => config.open()}
			class="relative gap-1.5"
			title="Configurar clave y modelo de OpenRouter"
		>
			<Settings class="w-4 h-4 text-gray-500" />
			<span>Ajustes IA</span>
			{#if !config.hasKey}
				<span class="w-2 h-2 rounded-full bg-amber-500 absolute -top-0.5 -right-0.5"></span>
			{/if}
		</Button>

		<Button
			variant="outline"
			size="sm"
			onclick={onRefresh}
			disabled={isFetching}
			title="Actualizar listado de remitos"
		>
			<RefreshCw class="w-4 h-4 text-gray-600 {isFetching ? 'animate-spin' : ''}" />
		</Button>

		<a href="/remitos/new">
			<Button size="sm" class="bg-emerald-600 hover:bg-emerald-700 text-white gap-1.5 shadow-xs">
				<Plus class="w-4 h-4" />
				<span>Nuevo Remito</span>
			</Button>
		</a>
	</div>
</div>
