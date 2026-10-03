<script lang="ts">
import {
	createMutation,
	createQuery,
	useQueryClient,
} from '@tanstack/svelte-query';
import {
	createTableState,
	renderSnippet,
	type SortingState,
} from '@tanstack/svelte-table';
import {
	type ProductResponse,
	type ProductType,
	productCreateApiV1ProductsPostMutation,
	productReadMultiApiV1ProductsGetOptions,
	productUpdateApiV1ProductsIdPatchMutation,
} from '@vitalcer/api';
import { formatARS, formatWeight } from '@vitalcer/core';
import { Badge, Button, Card, Dialog, Input, VirtualTable } from '@vitalcer/ui';
import {
	AlertCircle,
	CheckCircle2,
	Edit2,
	Layers,
	Plus,
	RefreshCw,
	Scale,
	Search,
} from 'lucide-svelte';
import { createAppColumnHelper, createAppTable } from '$lib/table';

const queryClient = useQueryClient();

const productsQuery = createQuery(() =>
	productReadMultiApiV1ProductsGetOptions({
		query: { limit: 1000 },
	}),
);

let searchTerm = $state('');
const [sorting, setSorting] = createTableState<SortingState>([]);

// Dialog State (Create / Edit)
let isDialogOpen = $state(false);
let editingProduct = $state<ProductResponse | null>(null);

// Form Fields
let formSku = $state('');
let formName = $state('');
let formProductType = $state<ProductType>('discrete');
let formUnitPrice = $state<number | ''>('');
let formBulkReferenceGrams = $state(100);
let formPluCode = $state('');
let formInitialStock = $state(0);
let formMinSafetyBuffer = $state(0);
let formIsActive = $state(true);
let formSyncPedidosya = $state(true);
let formSyncRappi = $state(true);
let formSyncVgo = $state(true);
let formSyncMercadolibre = $state(false);

let formError = $state<string | null>(null);
let successBanner = $state<string | null>(null);

const createProductMutation = createMutation(() =>
	productCreateApiV1ProductsPostMutation(),
);
const updateProductMutation = createMutation(() =>
	productUpdateApiV1ProductsIdPatchMutation(),
);

function openCreateModal() {
	editingProduct = null;
	formSku = '';
	formName = '';
	formProductType = 'discrete';
	formUnitPrice = '';
	formBulkReferenceGrams = 100;
	formPluCode = '';
	formInitialStock = 0;
	formMinSafetyBuffer = 0;
	formIsActive = true;
	formSyncPedidosya = true;
	formSyncRappi = true;
	formSyncVgo = true;
	formSyncMercadolibre = false;
	formError = null;
	isDialogOpen = true;
}

function openEditModal(prod: ProductResponse) {
	editingProduct = prod;
	formSku = prod.sku;
	formName = prod.name;
	formProductType = prod.product_type ?? 'discrete';
	formUnitPrice = prod.unit_price;
	formBulkReferenceGrams = prod.bulk_reference_grams ?? 100;
	formPluCode = prod.plu_code ?? '';
	formInitialStock = prod.current_stock;
	formMinSafetyBuffer = prod.min_safety_buffer ?? 0;
	formIsActive = prod.is_active ?? true;
	formSyncPedidosya = prod.sync_pedidosya ?? true;
	formSyncRappi = prod.sync_rappi ?? true;
	formSyncVgo = prod.sync_vgo ?? true;
	formSyncMercadolibre = prod.sync_mercadolibre ?? false;
	formError = null;
	isDialogOpen = true;
}

async function handleSaveProduct(e: SubmitEvent) {
	e.preventDefault();
	formError = null;

	if (
		!formSku.trim() ||
		!formName.trim() ||
		!formUnitPrice ||
		Number(formUnitPrice) <= 0
	) {
		formError = 'Completa SKU, nombre y precio unitario mayor a cero.';
		return;
	}

	if (
		formProductType === 'bulk' &&
		formPluCode.trim() &&
		!/^\d{4}$/.test(formPluCode.trim())
	) {
		formError =
			'El código PLU para balanza debe ser numérico de 4 dígitos (ej: 0142).';
		return;
	}

	try {
		if (editingProduct) {
			// Edit existing product
			await updateProductMutation.mutateAsync({
				path: { id: editingProduct.id },
				body: {
					sku: formSku.trim(),
					name: formName.trim(),
					product_type: formProductType,
					unit_price: Math.round(Number(formUnitPrice)),
					bulk_reference_grams:
						formProductType === 'bulk'
							? Number(formBulkReferenceGrams)
							: undefined,
					plu_code:
						formProductType === 'bulk' && formPluCode.trim()
							? formPluCode.trim()
							: null,
					min_safety_buffer: Number(formMinSafetyBuffer),
					is_active: formIsActive,
					sync_pedidosya: formSyncPedidosya,
					sync_rappi: formSyncRappi,
					sync_vgo: formSyncVgo,
					sync_mercadolibre: formSyncMercadolibre,
				},
			});
			successBanner = `Artículo "${formName}" actualizado correctamente.`;
		} else {
			// Create new product
			await createProductMutation.mutateAsync({
				body: {
					sku: formSku.trim(),
					name: formName.trim(),
					product_type: formProductType,
					unit_price: Math.round(Number(formUnitPrice)),
					bulk_reference_grams:
						formProductType === 'bulk' ? Number(formBulkReferenceGrams) : 100,
					plu_code:
						formProductType === 'bulk' && formPluCode.trim()
							? formPluCode.trim()
							: null,
					current_stock: Number(formInitialStock),
					min_safety_buffer: Number(formMinSafetyBuffer),
					is_active: formIsActive,
					sync_pedidosya: formSyncPedidosya,
					sync_rappi: formSyncRappi,
					sync_vgo: formSyncVgo,
					sync_mercadolibre: formSyncMercadolibre,
				},
			});
			successBanner = `Artículo "${formName}" creado exitosamente en el catálogo.`;
		}

		await queryClient.invalidateQueries();
		isDialogOpen = false;
		setTimeout(() => {
			successBanner = null;
		}, 5000);
	} catch (err: unknown) {
		formError =
			err instanceof Error ? err.message : 'Error al guardar el producto.';
	}
}

const products = $derived<ProductResponse[]>(
	productsQuery.data && 'data' in productsQuery.data
		? productsQuery.data.data
		: [],
);

const filteredProducts = $derived(
	products.filter((p) => {
		const term = searchTerm.toLowerCase().trim();
		if (!term) return true;
		return (
			p.name.toLowerCase().includes(term) ||
			p.sku.toLowerCase().includes(term) ||
			Boolean(p.plu_code?.toLowerCase().includes(term))
		);
	}),
);

// Summary Metrics
const totalProducts = $derived(products.length);
const bulkProducts = $derived(
	products.filter((p) => p.product_type === 'bulk').length,
);
const discreteProducts = $derived(
	products.filter((p) => p.product_type === 'discrete').length,
);
const lowStockProducts = $derived(
	products.filter((p) => p.current_stock <= 0).length,
);

const columnHelper = createAppColumnHelper<ProductResponse>();

const columns = columnHelper.columns([
	columnHelper.accessor('sku', {
		header: 'SKU / Código',
		cell: (info) => info.getValue(),
	}),
	columnHelper.accessor('plu_code', {
		header: 'PLU',
		cell: (info) => info.getValue() ?? '—',
	}),
	columnHelper.accessor('name', {
		header: 'Nombre del Producto',
		cell: (info) => info.getValue(),
	}),
	columnHelper.accessor('product_type', {
		header: 'Tipo',
		cell: (info) => renderSnippet(typeCellSnippet, info.getValue()),
	}),
	columnHelper.accessor('unit_price', {
		header: 'Precio Unitario',
		cell: (info) => formatARS(info.getValue()),
	}),
	columnHelper.accessor('current_stock', {
		header: 'Stock Físico',
		cell: (info) => {
			const row = info.row.original;
			return row.product_type === 'bulk'
				? formatWeight(info.getValue())
				: `${info.getValue()} u`;
		},
	}),
	columnHelper.accessor('reserved_stock', {
		header: 'Reservado',
		cell: (info) => {
			const row = info.row.original;
			const val = info.getValue();
			if (!val) return '0';
			return row.product_type === 'bulk' ? formatWeight(val) : `${val} u`;
		},
	}),
	columnHelper.accessor('virtual_stock', {
		header: 'Stock Virtual',
		cell: (info) => {
			const row = info.row.original;
			const val = info.getValue();
			return row.product_type === 'bulk' ? formatWeight(val) : `${val} u`;
		},
	}),
	columnHelper.accessor('is_active', {
		header: 'Estado',
		cell: (info) => renderSnippet(statusCellSnippet, info.getValue()),
	}),
	columnHelper.display({
		id: 'actions',
		header: 'Acciones',
		cell: (info) => renderSnippet(actionsCellSnippet, info.row.original),
	}),
]);

const table = createAppTable({
	columns,
	get data() {
		return filteredProducts;
	},
	state: {
		get sorting() {
			return sorting();
		},
	},
	onSortingChange: setSorting,
});
</script>

{#snippet typeCellSnippet(type: string | undefined)}
  {#if type === 'bulk'}
    <Badge variant="success">Granel</Badge>
  {:else}
    <Badge variant="default">Discreto</Badge>
  {/if}
{/snippet}

{#snippet statusCellSnippet(active: boolean | undefined)}
  {#if active}
    <Badge variant="success">Activo</Badge>
  {:else}
    <Badge variant="destructive">Inactivo</Badge>
  {/if}
{/snippet}

{#snippet actionsCellSnippet(product: ProductResponse)}
  <div class="flex items-center gap-3">
    <button
      type="button"
      onclick={() => openEditModal(product)}
      class="text-xs text-emerald-700 hover:text-emerald-900 font-medium inline-flex items-center gap-1 cursor-pointer"
    >
      <Edit2 class="w-3 h-3" />
      <span>Editar</span>
    </button>
    <a
      href="/ledger?product_id={product.id}"
      class="text-xs text-blue-600 hover:text-blue-800 underline font-medium"
    >
      Ledger
    </a>
  </div>
{/snippet}

<div class="space-y-6">
  <!-- Top Title & Controls -->
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <div>
      <h1 class="text-xl font-bold tracking-tight text-gray-900">Catálogo de Productos</h1>
      <p class="text-xs text-gray-500 mt-1">
        Consulta y administración de maestros de artículos, precios en ARS y sincronización de stock.
      </p>
    </div>

    <div class="flex items-center gap-2">
      <Button
        variant="primary"
        size="sm"
        onclick={openCreateModal}
      >
        <Plus class="w-3.5 h-3.5" />
        <span>Nuevo Producto</span>
      </Button>

      <Button
        variant="outline"
        size="sm"
        onclick={() => productsQuery.refetch()}
        disabled={productsQuery.isFetching}
      >
        <RefreshCw class="w-3.5 h-3.5 {productsQuery.isFetching ? 'animate-spin' : ''}" />
        <span>Actualizar</span>
      </Button>
    </div>
  </div>

  <!-- Success Notification -->
  {#if successBanner}
    <Card class="p-3 bg-emerald-50 border-emerald-200">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2 text-emerald-900 text-xs font-medium">
          <CheckCircle2 class="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successBanner}</span>
        </div>
        <button
          type="button"
          onclick={() => (successBanner = null)}
          class="text-xs text-emerald-600 hover:text-emerald-800 cursor-pointer"
        >
          Cerrar
        </button>
      </div>
    </Card>
  {/if}

  <!-- Summary Cards -->
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
    <Card class="p-3">
      <div class="flex items-center justify-between">
        <span class="text-xs text-gray-500">Total Artículos</span>
        <Layers class="w-4 h-4 text-gray-400" />
      </div>
      <p class="text-lg font-bold text-gray-900 font-mono mt-1">{totalProducts}</p>
    </Card>

    <Card class="p-3">
      <div class="flex items-center justify-between">
        <span class="text-xs text-gray-500">Granel (Pesables)</span>
        <Scale class="w-4 h-4 text-emerald-600" />
      </div>
      <p class="text-lg font-bold text-emerald-700 font-mono mt-1">{bulkProducts}</p>
    </Card>

    <Card class="p-3">
      <div class="flex items-center justify-between">
        <span class="text-xs text-gray-500">Unitarios (Discretos)</span>
        <Layers class="w-4 h-4 text-blue-600" />
      </div>
      <p class="text-lg font-bold text-blue-700 font-mono mt-1">{discreteProducts}</p>
    </Card>

    <Card class="p-3">
      <div class="flex items-center justify-between">
        <span class="text-xs text-gray-500">Sin Stock (Físico &le; 0)</span>
        <AlertCircle class="w-4 h-4 text-rose-500" />
      </div>
      <p class="text-lg font-bold text-rose-600 font-mono mt-1">{lowStockProducts}</p>
    </Card>
  </div>

  <!-- Filter Bar -->
  <div class="flex items-center gap-3">
    <div class="relative flex-1 max-w-sm">
      <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
      <Input
        type="search"
        placeholder="Buscar por SKU, PLU o nombre..."
        class="pl-8"
        bind:value={searchTerm}
      />
    </div>
    {#if searchTerm}
      <span class="text-xs text-gray-500">
        Mostrando {filteredProducts.length} de {totalProducts}
      </span>
    {/if}
  </div>

  <!-- Virtualized Data Table -->
  {#if productsQuery.isPending}
    <div class="h-96 border border-gray-200 rounded-md bg-white flex items-center justify-center text-sm text-gray-400">
      Cargando catálogo de productos...
    </div>
  {:else if productsQuery.isError}
    <div class="h-96 border border-rose-200 rounded-md bg-rose-50 p-6 flex flex-col items-center justify-center text-center">
      <AlertCircle class="w-8 h-8 text-rose-500 mb-2" />
      <p class="text-sm font-medium text-rose-900">Error al cargar productos</p>
      <p class="text-xs text-rose-600 mt-1">
        {((productsQuery.error as any)?.message) ?? 'Verifica la conexión con el servidor backend'}
      </p>
      <Button variant="outline" size="sm" class="mt-4" onclick={() => productsQuery.refetch()}>
        Reintentar
      </Button>
    </div>
  {:else}
    <VirtualTable {table} height="600px" />
  {/if}
</div>

<!-- ================= Product Create / Edit Dialog ================= -->
<Dialog
  bind:open={isDialogOpen}
  title={editingProduct ? 'Editar Producto' : 'Crear Nuevo Producto'}
  description={editingProduct ? 'Modifica los datos del artículo seleccionado.' : 'Registra un nuevo artículo discreto o a granel en el sistema.'}
>
  {#snippet children()}
    <form id="productForm" onsubmit={handleSaveProduct} class="space-y-4">
      {#if formError}
        <div class="p-2.5 bg-rose-50 border border-rose-200 rounded-md flex items-center gap-2 text-rose-800 text-xs">
          <AlertCircle class="w-4 h-4 text-rose-600 shrink-0" />
          <span>{formError}</span>
        </div>
      {/if}

      <!-- Basic Info -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label for="prod-sku" class="block text-xs font-semibold text-gray-700 mb-1">
            SKU / Código de Barras *
          </label>
          <Input
            id="prod-sku"
            placeholder="Ej: 7791234567890 o ALF-01"
            bind:value={formSku}
            required
          />
        </div>

        <div>
          <label for="prod-type" class="block text-xs font-semibold text-gray-700 mb-1">
            Tipo de Artículo *
          </label>
          <select
            id="prod-type"
            bind:value={formProductType}
            class="w-full h-9 rounded-md border border-gray-200 bg-white px-3 py-1 text-sm text-gray-900 shadow-xs focus:outline-none focus:border-emerald-600"
          >
            <option value="discrete">Unidad (Discreto)</option>
            <option value="bulk">Pesable / Granel (Balanza)</option>
          </select>
        </div>
      </div>

      <div>
        <label for="prod-name" class="block text-xs font-semibold text-gray-700 mb-1">
          Nombre del Producto *
        </label>
        <Input
          id="prod-name"
          placeholder="Ej: Almendras Nonpareil o Alfajor Choco"
          bind:value={formName}
          required
        />
      </div>

      <!-- Bulk specific fields -->
      {#if formProductType === 'bulk'}
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3 bg-emerald-50/50 rounded-md border border-emerald-100">
          <div>
            <label for="prod-plu" class="block text-xs font-semibold text-emerald-900 mb-1">
              Código PLU Balanza (4 dígitos)
            </label>
            <Input
              id="prod-plu"
              maxlength={4}
              placeholder="Ej: 0142"
              bind:value={formPluCode}
            />
            <span class="text-[10px] text-emerald-700 mt-0.5 block">Para balanza EAN-13 (prefijo 20)</span>
          </div>

          <div>
            <label for="prod-ref-grams" class="block text-xs font-semibold text-emerald-900 mb-1">
              Gramos de Referencia
            </label>
            <Input
              id="prod-ref-grams"
              type="number"
              min="1"
              bind:value={formBulkReferenceGrams}
              required
            />
            <span class="text-[10px] text-emerald-700 mt-0.5 block">Precio expresado cada N gramos (ej: 100g)</span>
          </div>
        </div>
      {/if}

      <!-- Pricing & Initial Stock -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label for="prod-price" class="block text-xs font-semibold text-gray-700 mb-1">
            {formProductType === 'bulk' ? `Precio por ${formBulkReferenceGrams}g ($ ARS) *` : 'Precio por Unidad ($ ARS) *'}
          </label>
          <Input
            id="prod-price"
            type="number"
            min="1"
            placeholder="Ej: 1500"
            bind:value={formUnitPrice}
            required
          />
        </div>

        {#if !editingProduct}
          <div>
            <label for="prod-stock" class="block text-xs font-semibold text-gray-700 mb-1">
              Stock Inicial ({formProductType === 'bulk' ? 'Gramos' : 'Unidades'})
            </label>
            <Input
              id="prod-stock"
              type="number"
              min="0"
              bind:value={formInitialStock}
            />
          </div>
        {:else}
          <div>
            <label for="prod-buffer" class="block text-xs font-semibold text-gray-700 mb-1">
              Buffer Seguridad (Delivery)
            </label>
            <Input
              id="prod-buffer"
              type="number"
              min="0"
              bind:value={formMinSafetyBuffer}
            />
          </div>
        {/if}
      </div>

      <!-- Buffer if creating -->
      {#if !editingProduct}
        <div>
          <label for="prod-buffer-create" class="block text-xs font-semibold text-gray-700 mb-1">
            Buffer de Seguridad (withheld from delivery platforms)
          </label>
          <Input
            id="prod-buffer-create"
            type="number"
            min="0"
            bind:value={formMinSafetyBuffer}
          />
        </div>
      {/if}

      <!-- Status & Channels -->
      <div class="pt-2 border-t border-gray-100 space-y-2">
        <label class="flex items-center gap-2 cursor-pointer text-xs font-semibold text-gray-800">
          <input
            type="checkbox"
            bind:checked={formIsActive}
            class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
          />
          <span>Artículo Activo / Disponible para venta</span>
        </label>

        <div class="text-[11px] text-gray-500 font-medium pt-1">Sincronización con canales:</div>
        <div class="flex flex-wrap gap-4 text-xs text-gray-700">
          <label class="flex items-center gap-1.5 cursor-pointer">
            <input type="checkbox" bind:checked={formSyncPedidosya} class="rounded border-gray-300 text-emerald-600" />
            <span>PedidosYa</span>
          </label>
          <label class="flex items-center gap-1.5 cursor-pointer">
            <input type="checkbox" bind:checked={formSyncRappi} class="rounded border-gray-300 text-emerald-600" />
            <span>Rappi</span>
          </label>
          <label class="flex items-center gap-1.5 cursor-pointer">
            <input type="checkbox" bind:checked={formSyncVgo} class="rounded border-gray-300 text-emerald-600" />
            <span>VGO</span>
          </label>
          <label class="flex items-center gap-1.5 cursor-pointer">
            <input type="checkbox" bind:checked={formSyncMercadolibre} class="rounded border-gray-300 text-emerald-600" />
            <span>MercadoLibre</span>
          </label>
        </div>
      </div>
    </form>
  {/snippet}

  {#snippet footer()}
    <Button
      variant="outline"
      size="sm"
      type="button"
      onclick={() => (isDialogOpen = false)}
    >
      Cancelar
    </Button>
    <Button
      size="sm"
      type="submit"
      form="productForm"
      disabled={createProductMutation.isPending || updateProductMutation.isPending}
    >
      {createProductMutation.isPending || updateProductMutation.isPending ? 'Guardando...' : (editingProduct ? 'Guardar Cambios' : 'Crear Producto')}
    </Button>
  {/snippet}
</Dialog>
