<script lang="ts">
import { createQuery } from '@tanstack/svelte-query';
import {
	createTableState,
	renderSnippet,
	type SortingState,
} from '@tanstack/svelte-table';
import {
	auditProductStockOptions,
	getInventoryLedgerOptions,
	type InventoryLedgerResponse,
	type InventoryMovementType,
} from '@vitalcer/api';
import { Badge, Button, Card, Input, VirtualTable } from '@vitalcer/ui';
import {
	AlertTriangle,
	ArrowDownLeft,
	ArrowUpRight,
	RefreshCw,
	ShieldCheck,
} from 'lucide-svelte';
import { page } from '$app/state';
import { createAppColumnHelper, createAppTable } from '$lib/table';

// Read initial product_id from URL query param if navigated from catalog
const initialProductId = page.url.searchParams.get('product_id');

let productIdInput = $state(initialProductId ?? '');
let selectedMovementType = $state<string>('');
const [sorting, setSorting] = createTableState<SortingState>([
	{ id: 'id', desc: true },
]);

const activeProductId = $derived.by(() => {
	const num = Number(productIdInput.trim());
	return !Number.isNaN(num) && num > 0 ? num : undefined;
});

// Query Ledger
const ledgerQuery = createQuery(() =>
	getInventoryLedgerOptions({
		query: {
			product_id: activeProductId ?? null,
			movement_type: (selectedMovementType as InventoryMovementType) || null,
			limit: 500,
		},
	}),
);

// Optional Audit Query when single product is selected
const auditQuery = createQuery(() => ({
	...auditProductStockOptions({
		path: { product_id: activeProductId ?? 0 },
	}),
	enabled: !!activeProductId,
}));

const ledgerRecords = $derived<InventoryLedgerResponse[]>(
	Array.isArray(ledgerQuery.data) ? ledgerQuery.data : [],
);

const columnHelper = createAppColumnHelper<InventoryLedgerResponse>();

const columns = columnHelper.columns([
	columnHelper.accessor('id', {
		header: 'ID',
		cell: (info) => `#${info.getValue()}`,
	}),
	columnHelper.accessor('created_at', {
		header: 'Fecha / Hora',
		cell: (info) => {
			const d = new Date(info.getValue());
			return Number.isNaN(d.getTime())
				? info.getValue()
				: d.toLocaleString('es-AR', {
						dateStyle: 'short',
						timeStyle: 'medium',
					});
		},
	}),
	columnHelper.accessor('product_id', {
		header: 'ID Art.',
		cell: (info) => renderSnippet(productLinkSnippet, info.getValue()),
	}),
	columnHelper.accessor('movement_type', {
		header: 'Tipo Movimiento',
		cell: (info) => renderSnippet(movementTypeSnippet, info.getValue()),
	}),
	columnHelper.accessor('quantity_delta', {
		header: 'Variación (Δ)',
		cell: (info) => renderSnippet(deltaSnippet, info.getValue()),
	}),
	columnHelper.accessor('balance_after', {
		header: 'Balance Posterior',
		cell: (info) => `${info.getValue()}`,
	}),
	columnHelper.accessor('reference_id', {
		header: 'Referencia / Ticket',
		cell: (info) => info.getValue() || '—',
	}),
	columnHelper.accessor('notes', {
		header: 'Observaciones',
		cell: (info) => info.getValue() || '—',
	}),
]);

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
</script>

{#snippet productLinkSnippet(productId: number)}
  <button
    type="button"
    class="font-mono text-xs font-semibold text-blue-600 hover:text-blue-800 hover:underline cursor-pointer"
    onclick={() => {
      productIdInput = String(productId);
    }}
  >
    Art #{productId}
  </button>
{/snippet}

{#snippet movementTypeSnippet(type: InventoryMovementType)}
  {#if type === 'receiving'}
    <Badge variant="success">Entrada Proveedor</Badge>
  {:else if type === 'sale_pos'}
    <Badge variant="default">Venta Mostrador</Badge>
  {:else if type === 'delivery_fulfilled'}
    <Badge variant="outline">Delivery</Badge>
  {:else if type === 'shrinkage_merma'}
    <Badge variant="destructive">Merma / Pérdida</Badge>
  {:else if type === 'manual_adjustment'}
    <Badge variant="warning">Ajuste Manual</Badge>
  {:else}
    <Badge variant="default">{type}</Badge>
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

<div class="space-y-6">
  <!-- Header -->
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <div>
      <h1 class="text-xl font-bold tracking-tight text-gray-900">Lista general de stock</h1>
      <p class="text-xs text-gray-500 mt-1">
        Historial de stock
      </p>
    </div>

    <div class="flex items-center gap-2">
      <Button
        variant="outline"
        size="sm"
        onclick={() => {
          ledgerQuery.refetch();
          if (activeProductId) auditQuery.refetch();
        }}
        disabled={ledgerQuery.isFetching}
      >
        <RefreshCw class="w-3.5 h-3.5 {ledgerQuery.isFetching ? 'animate-spin' : ''}" />
        <span>Actualizar</span>
      </Button>
    </div>
  </div>

  <!-- Product Audit Card (when single product is selected) -->
  {#if activeProductId && auditQuery.data}
    {@const audit = auditQuery.data}
    <Card class="p-4 border-l-4 {audit.is_reconciled ? 'border-l-emerald-500 bg-emerald-50/30' : 'border-l-rose-500 bg-rose-50/30'}">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2">
            {#if audit.is_reconciled}
              <ShieldCheck class="w-5 h-5 text-emerald-600" />
              <span class="font-bold text-emerald-900 text-sm">Stock Consistente / Sin Desvío</span>
            {:else}
              <AlertTriangle class="w-5 h-5 text-rose-600" />
              <span class="font-bold text-rose-900 text-sm">¡Alerta de Desvío en Auditoría!</span>
            {/if}
            <span class="text-xs font-mono text-gray-600">[{audit.sku}] {audit.name}</span>
          </div>

          <div class="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-xs text-gray-600 font-mono">
            <span>Stock Físico Actual: <strong class="text-gray-900">{audit.current_stock}</strong></span>
            <span>Suma de Ledger: <strong class="text-gray-900">{audit.ledger_calculated_balance}</strong></span>
            <span>Reservado Delivery: <strong class="text-gray-900">{audit.reserved_stock}</strong></span>
            <span>Stock Virtual Libre: <strong class="text-gray-900">{audit.virtual_stock}</strong></span>
            <span>Desvío (Drift): <strong class={audit.drift === 0 ? 'text-emerald-700' : 'text-rose-700'}>{audit.drift}</strong></span>
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          class="self-start md:self-auto text-xs"
          onclick={() => {
            productIdInput = '';
          }}
        >
          Limpiar Filtro
        </Button>
      </div>
    </Card>
  {/if}

  <!-- Filter Bar -->
  <div class="flex flex-wrap items-center gap-3">
    <div class="w-48">
      <Input
        type="number"
        placeholder="Filtrar por ID Prod..."
        bind:value={productIdInput}
      />
    </div>

    <div class="w-56">
      <select
        bind:value={selectedMovementType}
        class="w-full h-9 rounded-md border border-gray-200 bg-white px-3 py-1 text-sm text-gray-800 shadow-xs focus:outline-none focus:border-emerald-600"
      >
        <option value="">Todos los movimientos</option>
        <option value="receiving">Entrada Proveedor</option>
        <option value="sale_pos">Venta Mostrador</option>
        <option value="delivery_fulfilled">Delivery</option>
        <option value="shrinkage_merma">Merma / Pérdida</option>
        <option value="manual_adjustment">Ajuste Manual</option>
      </select>
    </div>

    {#if activeProductId || selectedMovementType}
      <Button
        variant="ghost"
        size="sm"
        onclick={() => {
          productIdInput = '';
          selectedMovementType = '';
        }}
      >
        Restablecer Filtros
      </Button>
    {/if}

    <span class="text-xs text-gray-500 ml-auto font-mono">
      {ledgerRecords.length} movimientos
    </span>
  </div>

  <!-- Virtualized Data Table -->
  {#if ledgerQuery.isPending}
    <div class="h-96 border border-gray-200 rounded-md bg-white flex items-center justify-center text-sm text-gray-400">
      Cargando lista...
    </div>
  {:else if ledgerQuery.isError}
    <div class="h-96 border border-rose-200 rounded-md bg-rose-50 p-6 flex flex-col items-center justify-center text-center">
      <AlertTriangle class="w-8 h-8 text-rose-500 mb-2" />
      <p class="text-sm font-medium text-rose-900">Error al cargar lista de stock</p>
      <p class="text-xs text-rose-600 mt-1">
        {((ledgerQuery.error as any)?.message) ?? 'Verifica la conexión con el servidor backend'}
      </p>
      <Button variant="outline" size="sm" class="mt-4" onclick={() => ledgerQuery.refetch()}>
        Reintentar
      </Button>
    </div>
  {:else}
    <VirtualTable {table} height="600px" />
  {/if}
</div>
