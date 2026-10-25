<script lang="ts">
import {
	createMutation,
	createQuery,
	useQueryClient,
} from '@tanstack/svelte-query';
import { createTableState, type SortingState } from '@tanstack/svelte-table';
import {
	type ProductResponse,
	productCreateApiV1ProductsPostMutation,
	productReadMultiApiV1ProductsGetOptions,
	productUpdateApiV1ProductsIdPatchMutation,
} from '@vitalcer/api';
import { Badge, Button, Card, VirtualTable } from '@vitalcer/ui';
import { AlertCircle, CheckCircle2, Edit2 } from 'lucide-svelte';
import {
	calculateCatalogMetrics,
	filterProducts,
} from '$lib/catalog/catalog-filter';
import { createCatalogColumns } from '$lib/catalog/columns';
import CatalogFilterBar from '$lib/catalog/components/CatalogFilterBar.svelte';
import CatalogHeader from '$lib/catalog/components/CatalogHeader.svelte';
import CatalogMetricsCards from '$lib/catalog/components/CatalogMetricsCards.svelte';
import ProductFormDialog from '$lib/catalog/components/ProductFormDialog.svelte';
import { ProductFormState } from '$lib/catalog/product-form.svelte';
import { createAppTable } from '$lib/table';

const queryClient = useQueryClient();

const productsQuery = createQuery(() =>
	productReadMultiApiV1ProductsGetOptions({
		query: { limit: 1000 },
	}),
);

const createProductMutation = createMutation(() =>
	productCreateApiV1ProductsPostMutation(),
);
const updateProductMutation = createMutation(() =>
	productUpdateApiV1ProductsIdPatchMutation(),
);

let searchTerm = $state('');
const [sorting, setSorting] = createTableState<SortingState>([]);
const form = new ProductFormState();
let successBanner = $state<string | null>(null);

const products = $derived<ProductResponse[]>(
	productsQuery.data && 'data' in productsQuery.data
		? (productsQuery.data.data as ProductResponse[])
		: Array.isArray(productsQuery.data)
			? (productsQuery.data as ProductResponse[])
			: [],
);

const filteredProducts = $derived(filterProducts(products, searchTerm));
const metrics = $derived(calculateCatalogMetrics(products));

async function handleSaveProduct(e: SubmitEvent) {
	e.preventDefault();
	if (!form.validate()) return;

	try {
		if (form.editingProduct) {
			await updateProductMutation.mutateAsync({
				path: { id: form.editingProduct.id },
				body: form.buildUpdatePayload(),
			});
			successBanner = `Artículo "${form.name}" actualizado correctamente.`;
		} else {
			await createProductMutation.mutateAsync({
				body: form.buildCreatePayload(),
			});
			successBanner = `Artículo "${form.name}" creado exitosamente en el catálogo.`;
		}

		await queryClient.invalidateQueries();
		form.close();
		setTimeout(() => {
			successBanner = null;
		}, 5000);
	} catch (err: unknown) {
		form.formError =
			err instanceof Error ? err.message : 'Error al guardar el producto.';
	}
}

const columns = createCatalogColumns({
	nameCell: nameCellSnippet,
	typeCell: typeCellSnippet,
	statusCell: statusCellSnippet,
	actionsCell: actionsCellSnippet,
});

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

{#snippet nameCellSnippet(product: ProductResponse)}
  <div class="flex flex-col py-0.5 max-w-[180px] xs:max-w-[220px] sm:max-w-none">
    <div class="flex items-center gap-1.5 flex-wrap">
      <span class="font-medium text-gray-900 leading-tight">{product.name}</span>
      <span class="md:hidden inline-flex items-center gap-1">
        {#if product.product_type === 'bulk'}
          <Badge variant="success" class="text-[9px] px-1 py-0">Granel</Badge>
        {/if}
        {#if !product.is_active}
          <Badge variant="destructive" class="text-[9px] px-1 py-0">Inactivo</Badge>
        {/if}
      </span>
    </div>
    <div class="text-[10px] sm:text-[11px] text-gray-400 font-mono flex items-center gap-1.5 mt-0.5 md:hidden">
      <span>{product.sku}</span>
      {#if product.plu_code}
        <span>• PLU {product.plu_code}</span>
      {/if}
    </div>
  </div>
{/snippet}

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
  <div class="flex items-center gap-2 sm:gap-3">
    <button
      type="button"
      onclick={() => form.openEdit(product)}
      class="text-xs text-emerald-700 hover:text-emerald-900 font-medium inline-flex items-center gap-1 cursor-pointer p-1 -m-1"
      title="Editar producto"
    >
      <Edit2 class="w-3.5 h-3.5" />
      <span class="hidden sm:inline">Editar</span>
    </button>
    <a
      href="/ledger?product_id={product.id}"
      class="text-xs text-blue-600 hover:text-blue-800 underline font-medium p-1 -m-1"
      title="Ver movimientos en ledger"
    >
      Ledger
    </a>
  </div>
{/snippet}

<div class="space-y-4 sm:space-y-6 min-w-0">
  <CatalogHeader
    isFetching={productsQuery.isFetching}
    onNewProduct={() => form.openCreate()}
    onRefresh={() => productsQuery.refetch()}
  />

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
          class="text-xs text-emerald-600 hover:text-emerald-800 cursor-pointer p-1"
        >
          Cerrar
        </button>
      </div>
    </Card>
  {/if}

  <CatalogMetricsCards {metrics} />

  <CatalogFilterBar
    bind:searchTerm
    filteredCount={filteredProducts.length}
    totalCount={metrics.total}
  />

  {#if productsQuery.isPending}
    <div class="h-80 sm:h-96 border border-gray-200 rounded-md bg-white flex items-center justify-center text-sm text-gray-400">
      Cargando catálogo de productos...
    </div>
  {:else if productsQuery.isError}
    <div class="h-80 sm:h-96 border border-rose-200 rounded-md bg-rose-50 p-6 flex flex-col items-center justify-center text-center">
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
    <VirtualTable {table} height="calc(100vh - 330px)" class="min-h-[400px]" />
  {/if}
</div>

<ProductFormDialog
  {form}
  isSubmitting={createProductMutation.isPending || updateProductMutation.isPending}
  onSubmit={handleSaveProduct}
/>
