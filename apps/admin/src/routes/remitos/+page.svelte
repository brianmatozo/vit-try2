<script lang="ts">
import { createQuery, useQueryClient } from '@tanstack/svelte-query';
import {
	listRemitosApiV1RemitosGetOptions,
	type RemitoResponse,
} from '@vitalcer/api';
import { Card } from '@vitalcer/ui';
import { RefreshCw } from 'lucide-svelte';
import RemitoConfigDialog from '$lib/remitos/components/RemitoConfigDialog.svelte';
import RemitoFilterBar from '$lib/remitos/components/RemitoFilterBar.svelte';
import RemitoKpiCards from '$lib/remitos/components/RemitoKpiCards.svelte';
import RemitoListHeader from '$lib/remitos/components/RemitoListHeader.svelte';
import RemitoTable from '$lib/remitos/components/RemitoTable.svelte';
import { RemitoConfigState } from '$lib/remitos/remito-config-state.svelte';
import { RemitosState } from '$lib/remitos/remitos-state.svelte';

const queryClient = useQueryClient();
const remitosState = new RemitosState();
const config = new RemitoConfigState();

const remitosQuery = createQuery(() =>
	listRemitosApiV1RemitosGetOptions({
		query: { limit: 100 },
	}),
);

$effect(() => {
	const raw = remitosQuery.data;
	remitosState.remitosList = Array.isArray(raw)
		? (raw as RemitoResponse[])
		: [];
});

async function handleRefresh(): Promise<void> {
	await queryClient.invalidateQueries({
		queryKey: ['listRemitosApiV1RemitosGet'],
	});
}
</script>

<svelte:head>
	<title>Remitos & Recepción | Vitalcer Admin</title>
</svelte:head>

<div class="space-y-6">
	<!-- Page Header -->
	<RemitoListHeader
		{config}
		isFetching={remitosQuery.isFetching}
		onRefresh={handleRefresh}
	/>

	<!-- KPI Summary Metrics -->
	<RemitoKpiCards kpis={remitosState.kpis} />

	<!-- Filter & Tab Switcher Bar -->
	<RemitoFilterBar
		bind:searchTerm={remitosState.searchTerm}
		activeTab={remitosState.activeTab}
		stagedCount={remitosState.kpis.stagedCount}
		committedCount={remitosState.kpis.committedCount}
		totalCount={remitosState.remitosList.length}
		onTabChange={(tab) => remitosState.setTab(tab)}
		onClear={() => remitosState.clearSearch()}
	/>

	<!-- Content Area -->
	{#if remitosQuery.isLoading}
		<Card class="p-12 text-center">
			<RefreshCw class="w-8 h-8 text-emerald-600 animate-spin mx-auto mb-3" />
			<div class="text-sm font-semibold text-gray-700">Cargando comprobantes...</div>
			<div class="text-xs text-gray-400 mt-1">Consultando base de remitos ingresados</div>
		</Card>
	{:else}
		<RemitoTable remitos={remitosState.filteredRemitos} />
	{/if}

	<!-- OpenRouter Configuration Modal -->
	<RemitoConfigDialog {config} />
</div>
