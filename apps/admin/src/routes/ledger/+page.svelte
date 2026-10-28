<script lang="ts">
import { createQuery } from '@tanstack/svelte-query';
import { createTableState, type SortingState } from '@tanstack/svelte-table';
import {
	auditProductStockOptions,
	getInventoryLedgerOptions,
	type InventoryLedgerResponse,
	type InventoryMovementType,
} from '@vitalcer/api';
import { Badge, Button, VirtualTable } from '@vitalcer/ui';
import { AlertTriangle, ArrowDownLeft, ArrowUpRight } from 'lucide-svelte';
import { page } from '$app/state';
import { createLedgerColumns } from '$lib/ledger/columns';
import LedgerFilterBar from '$lib/ledger/components/LedgerFilterBar.svelte';
import LedgerHeader from '$lib/ledger/components/LedgerHeader.svelte';
import ProductAuditCard from '$lib/ledger/components/ProductAuditCard.svelte';
import { LedgerState } from '$lib/ledger/ledger-state.svelte';
import { createAppTable } from '$lib/table';

const initialProductId = page.url.searchParams.get('product_id');
const state = new LedgerState(initialProductId);

const [sorting, setSorting] = createTableState<SortingState>([
	{ id: 'id', desc: true },
]);

// Query Ledger
const ledgerQuery = createQuery(() =>
	getInventoryLedgerOptions({
		query: {
			product_id: state.activeProductId ?? null,
			movement_type:
				(state.selectedMovementType as InventoryMovementType) || null,
			limit: 500,
		},
	}),
);

// Optional Audit Query when single product is selected
const auditQuery = createQuery(() => ({
	...auditProductStockOptions({
		path: { product_id: state.activeProductId ?? 0 },
	}),
	enabled: !!state.activeProductId,
}));

const ledgerRecords = $derived<InventoryLedgerResponse[]>(
	Array.isArray(ledgerQuery.data) ? ledgerQuery.data : [],
);

const columns = createLedgerColumns({
	productLinkSnippet,
	movementTypeSnippet,
	deltaSnippet,
});

const table = createAppTable({
	columns,
	get data() {
		return ledgerRecords;
	},
	state: {
		get sorting() {
			return sorting();
		},
	},
	onSortingChange: setSorting,
});

function handleRefresh() {
	ledgerQuery.refetch();
	if (state.activeProductId) {
		auditQuery.refetch();
	}
}
</script>

{#snippet productLinkSnippet(productId: number)}
  <button
    type="button"
    class="font-mono text-xs font-semibold text-blue-600 hover:text-blue-800 hover:underline cursor-pointer p-1 -m-1"
    onclick={() => {
      state.productIdInput = String(productId);
    }}
  >
    #{productId}
  </button>
{/snippet}

{#snippet movementTypeSnippet(type: InventoryMovementType)}
  {#if type === 'receiving'}
    <Badge variant="success" class="text-2xs sm:text-xs">Entrada</Badge>
  {:else if type === 'sale_pos'}
    <Badge variant="default" class="text-2xs sm:text-xs">Mostrador</Badge>
  {:else if type === 'delivery_fulfilled'}
    <Badge variant="outline" class="text-2xs sm:text-xs">Delivery</Badge>
  {:else if type === 'shrinkage_merma'}
    <Badge variant="destructive" class="text-2xs sm:text-xs">Merma</Badge>
  {:else if type === 'manual_adjustment'}
    <Badge variant="warning" class="text-2xs sm:text-xs">Ajuste</Badge>
  {:else}
    <Badge variant="default" class="text-2xs sm:text-xs">{type}</Badge>
  {/if}
{/snippet}

{#snippet deltaSnippet(delta: number)}
  {#if delta > 0}
    <span class="inline-flex items-center text-emerald-700 font-mono font-bold text-xs">
      <ArrowUpRight class="w-3.5 h-3.5 mr-0.5 inline" />
      +{delta}
    </span>
  {:else if delta < 0}
    <span class="inline-flex items-center text-rose-700 font-mono font-bold text-xs">
      <ArrowDownLeft class="w-3.5 h-3.5 mr-0.5 inline" />
      {delta}
    </span>
  {:else}
    <span class="text-gray-400 font-mono text-xs">0</span>
  {/if}
{/snippet}

<div class="space-y-4 sm:space-y-6 min-w-0">
  <LedgerHeader
    isFetching={ledgerQuery.isFetching}
    onRefresh={handleRefresh}
  />

  {#if state.activeProductId && auditQuery.data}
    <ProductAuditCard
      audit={auditQuery.data}
      onClear={() => {
        state.productIdInput = '';
      }}
    />
  {/if}

  <LedgerFilterBar
    bind:productIdInput={state.productIdInput}
    bind:selectedMovementType={state.selectedMovementType}
    hasActiveFilters={state.hasActiveFilters}
    recordCount={ledgerRecords.length}
    onReset={() => state.resetFilters()}
  />

  {#if ledgerQuery.isPending}
    <div class="h-80 sm:h-96 border border-gray-200 rounded-md bg-white flex items-center justify-center text-sm text-gray-400">
      Cargando lista de movimientos...
    </div>
  {:else if ledgerQuery.isError}
    <div class="h-80 sm:h-96 border border-rose-200 rounded-md bg-rose-50 p-6 flex flex-col items-center justify-center text-center">
      <AlertTriangle class="w-8 h-8 text-rose-500 mb-2" />
      <p class="text-sm font-medium text-rose-900">Error al cargar movimientos</p>
      <p class="text-xs text-rose-600 mt-1">
        {((ledgerQuery.error as any)?.message) ?? 'Verifica la conexión con el servidor backend'}
      </p>
      <Button variant="outline" size="sm" class="mt-4" onclick={() => ledgerQuery.refetch()}>
        Reintentar
      </Button>
    </div>
  {:else}
    <VirtualTable {table} height="calc(100vh - 300px)" class="min-h-96" />
  {/if}
</div>
