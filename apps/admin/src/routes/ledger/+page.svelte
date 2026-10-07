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
		meta: { className: 'hidden sm:table-cell' },
	}),
	columnHelper.accessor('created_at', {
		header: 'Fecha / Hora',
		cell: (info) => {
			const d = new Date(info.getValue());
			return Number.isNaN(d.getTime())
				? info.getValue()
				: d.toLocaleString('es-AR', {
						dateStyle: 'short',
						timeStyle: 'short',
					});
		},
	}),
	columnHelper.accessor('product_id', {
		header: 'Art.',
		cell: (info) => renderSnippet(productLinkSnippet, info.getValue()),
	}),
	columnHelper.accessor('movement_type', {
		header: 'Tipo',
		cell: (info) => renderSnippet(movementTypeSnippet, info.getValue()),
	}),
	columnHelper.accessor('quantity_delta', {
		header: 'Variación (Δ)',
		cell: (info) => renderSnippet(deltaSnippet, info.getValue()),
	}),
	columnHelper.accessor('balance_after', {
		header: 'Saldo',
		cell: (info) => `${info.getValue()}`,
	}),
	columnHelper.accessor('reference_id', {
		header: 'Referencia',
		cell: (info) => info.getValue() || '—',
		meta: { className: 'hidden md:table-cell' },
	}),
	columnHelper.accessor('notes', {
		header: 'Observaciones',
		cell: (info) => info.getValue() || '—',
		meta: { className: 'hidden lg:table-cell' },
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
    class="font-mono text-xs font-semibold text-blue-600 hover:text-blue-800 hover:underline cursor-pointer p-1 -m-1"
    onclick={() => {
      productIdInput = String(productId);
    }}
  >
    #{productId}
  </button>
{/snippet}

{#snippet movementTypeSnippet(type: InventoryMovementType)}
  {#if type === 'receiving'}
    <Badge variant="success" class="text-[10px] sm:text-xs">Entrada</Badge>
  {:else if type === 'sale_pos'}
    <Badge variant="default" class="text-[10px] sm:text-xs">Mostrador</Badge>
  {:else if type === 'delivery_fulfilled'}
    <Badge variant="outline" class="text-[10px] sm:text-xs">Delivery</Badge>
  {:else if type === 'shrinkage_merma'}
    <Badge variant="destructive" class="text-[10px] sm:text-xs">Merma</Badge>
  {:else if type === 'manual_adjustment'}
    <Badge variant="warning" class="text-[10px] sm:text-xs">Ajuste</Badge>
  {:else}
    <Badge variant="default" class="text-[10px] sm:text-xs">{type}</Badge>
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
  <!-- Header -->
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
    <div>
      <h1 class="text-lg sm:text-xl font-bold tracking-tight text-gray-900">Historial y Auditoría de Stock</h1>
      <p class="text-xs text-gray-500 mt-0.5 sm:mt-1">
        Registro inmutable de movimientos, auditoría de balance y detección de desvíos.
      </p>
    </div>

    <div class="flex items-center gap-2 w-full sm:w-auto">
      <Button
        variant="outline"
        size="sm"
        class="w-full sm:w-auto justify-center"
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
    <Card class="p-3 sm:p-4 border-l-4 {audit.is_reconciled ? 'border-l-emerald-500 bg-emerald-50/30' : 'border-l-rose-500 bg-rose-50/30'}">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 sm:gap-4">
        <div>
          <div class="flex items-center gap-2 flex-wrap">
            {#if audit.is_reconciled}
              <ShieldCheck class="w-4 h-4 sm:w-5 sm:h-5 text-emerald-600 shrink-0" />
              <span class="font-bold text-emerald-900 text-xs sm:text-sm">Stock Consistente</span>
            {:else}
              <AlertTriangle class="w-4 h-4 sm:w-5 sm:h-5 text-rose-600 shrink-0" />
              <span class="font-bold text-rose-900 text-xs sm:text-sm">¡Alerta de Desvío!</span>
            {/if}
            <span class="text-xs font-mono text-gray-600 font-medium">[{audit.sku}] {audit.name}</span>
          </div>

          <div class="mt-3 grid grid-cols-2 sm:flex sm:flex-wrap gap-2 sm:gap-x-6 sm:gap-y-1 text-xs text-gray-600 font-mono">
            <div class="bg-white/70 p-2 rounded sm:bg-transparent sm:p-0">
              Stock Físico: <strong class="text-gray-900">{audit.current_stock}</strong>
            </div>
            <div class="bg-white/70 p-2 rounded sm:bg-transparent sm:p-0">
              Suma Ledger: <strong class="text-gray-900">{audit.ledger_calculated_balance}</strong>
            </div>
            <div class="bg-white/70 p-2 rounded sm:bg-transparent sm:p-0">
              Reservado: <strong class="text-gray-900">{audit.reserved_stock}</strong>
            </div>
            <div class="bg-white/70 p-2 rounded sm:bg-transparent sm:p-0">
              Virtual Libre: <strong class="text-gray-900">{audit.virtual_stock}</strong>
            </div>
            <div class="bg-white/70 p-2 rounded sm:bg-transparent sm:p-0 col-span-2 sm:col-span-1">
              Desvío (Drift): <strong class={audit.drift === 0 ? 'text-emerald-700 font-bold' : 'text-rose-700 font-bold'}>{audit.drift}</strong>
            </div>
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          class="w-full sm:w-auto text-xs justify-center shrink-0"
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
  <div class="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
    <div class="w-full sm:w-48">
      <Input
        type="number"
        placeholder="Filtrar por ID Prod..."
        bind:value={productIdInput}
      />
    </div>

    <div class="w-full sm:w-56">
      <select
        bind:value={selectedMovementType}
        class="w-full h-10 sm:h-9 rounded-md border border-gray-300 bg-white px-3 py-1 text-base sm:text-sm text-gray-800 shadow-xs focus:outline-none focus:border-emerald-600"
      >
        <option value="">Todos los movimientos</option>
        <option value="receiving">Entrada Proveedor</option>
        <option value="sale_pos">Venta Mostrador</option>
        <option value="delivery_fulfilled">Delivery</option>
        <option value="shrinkage_merma">Merma / Pérdida</option>
        <option value="manual_adjustment">Ajuste Manual</option>
      </select>
    </div>

    <div class="flex items-center justify-between w-full sm:w-auto sm:ml-auto gap-2 pt-1 sm:pt-0">
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

      <span class="text-xs text-gray-500 font-mono ml-auto">
        {ledgerRecords.length} movimientos
      </span>
    </div>
  </div>

  <!-- Virtualized Data Table -->
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
    <VirtualTable {table} height="calc(100vh - 300px)" class="min-h-[400px]" />
  {/if}
</div>
