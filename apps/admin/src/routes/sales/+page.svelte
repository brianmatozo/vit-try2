<script lang="ts">
import { createQuery } from '@tanstack/svelte-query';
import {
	getInventoryLedgerOptions,
	type InventoryLedgerResponse,
	type ProductResponse,
	productReadMultiApiV1ProductsGetOptions,
} from '@vitalcer/api';
import { Card } from '@vitalcer/ui';
import { AlertCircle, RefreshCw } from 'lucide-svelte';
import SalesEmptyState from '$lib/sales/components/SalesEmptyState.svelte';
import SalesFilterBar from '$lib/sales/components/SalesFilterBar.svelte';
import SalesHeader from '$lib/sales/components/SalesHeader.svelte';
import SalesKpiCards from '$lib/sales/components/SalesKpiCards.svelte';
import SalesTicketCard from '$lib/sales/components/SalesTicketCard.svelte';
import { SalesState } from '$lib/sales/sales-state.svelte';

const state = new SalesState();

// Query completed POS sales from immutable ledger (staleTime: 0 ensures always fetching latest sales)
const ledgerQuery = createQuery(() => ({
	...getInventoryLedgerOptions({
		query: {
			movement_type: 'sale_pos',
			limit: 500,
		},
	}),
	staleTime: 0,
}));

// Query product catalog for name, SKU, and unit prices
const productsQuery = createQuery(() =>
	productReadMultiApiV1ProductsGetOptions({
		query: { limit: 1000 },
	}),
);

$effect(() => {
	state.ledgerEntries = Array.isArray(ledgerQuery.data)
		? (ledgerQuery.data as InventoryLedgerResponse[])
		: [];
});

$effect(() => {
	const raw = productsQuery.data;
	state.productsList =
		raw && 'data' in raw
			? (raw.data as ProductResponse[])
			: Array.isArray(raw)
				? (raw as ProductResponse[])
				: [];
});

async function handleRefresh() {
	await Promise.all([ledgerQuery.refetch(), productsQuery.refetch()]);
}
</script>

<svelte:head>
	<title>Ventas de Caja | Vitalcer Admin</title>
</svelte:head>

<div class="space-y-6">
	<!-- Page Header -->
	<SalesHeader
		isFetching={ledgerQuery.isFetching || productsQuery.isFetching}
		onRefresh={handleRefresh}
	/>

	<!-- KPI Summary Metrics -->
	<SalesKpiCards kpis={state.kpis} />

	<!-- Filter / Search Header -->
	<SalesFilterBar
		bind:searchTerm={state.searchTerm}
		filteredCount={state.filteredTickets.length}
		totalCount={state.tickets.length}
		onClearFilter={() => state.clearSearch()}
	/>

	<!-- Content State -->
	{#if ledgerQuery.isLoading || productsQuery.isLoading}
		<Card class="p-12 text-center">
			<RefreshCw class="w-8 h-8 text-emerald-600 animate-spin mx-auto mb-3" />
			<div class="text-sm font-semibold text-gray-700">Cargando historial de ventas...</div>
			<div class="text-xs text-gray-400 mt-1">Consultando registros del libro mayor de inventario</div>
		</Card>
	{:else if ledgerQuery.isError}
		<Card class="p-6 border-rose-200 bg-rose-50 text-rose-800">
			<div class="flex items-center gap-3">
				<AlertCircle class="w-5 h-5 text-rose-600 shrink-0" />
				<div>
					<div class="text-sm font-bold">Error al consultar las ventas</div>
					<div class="text-xs text-rose-600 mt-0.5">
						No se pudieron cargar los comprobantes desde el servidor. Verificá la conexión con la API.
					</div>
				</div>
			</div>
		</Card>
	{:else if state.filteredTickets.length === 0}
		<SalesEmptyState
			hasAnyTickets={state.tickets.length > 0}
			searchTerm={state.searchTerm}
		/>
	{:else}
		<!-- Tickets List -->
		<div class="space-y-3">
			{#each state.filteredTickets as ticket (ticket.ticketId)}
				<SalesTicketCard
					{ticket}
					isExpanded={state.isExpanded(ticket.ticketId)}
					onToggle={() => state.toggleExpand(ticket.ticketId)}
				/>
			{/each}
		</div>
	{/if}
</div>
