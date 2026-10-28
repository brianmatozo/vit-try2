<script lang="ts">
import { createQuery, useQueryClient } from '@tanstack/svelte-query';
import {
	confirmApiV1RemitosIdConfirmPost,
	getRemitoApiV1RemitosIdGetOptions,
	type ProductResponse,
	patchRemitoApiV1RemitosIdPatch,
	productCreateApiV1ProductsPost,
	productReadMultiApiV1ProductsGetOptions,
	type RemitoResponse,
	rejectApiV1RemitosIdRejectPost,
	updateItemApiV1RemitosIdItemsItemIdPut,
} from '@vitalcer/api';
import { Badge, Button, Card } from '@vitalcer/ui';
import {
	AlertCircle,
	ArrowLeft,
	CheckCircle,
	FileText,
	RefreshCw,
	XCircle,
} from 'lucide-svelte';
import { page } from '$app/state';
import RemitoDetailHeader from '$lib/remitos/components/RemitoDetailHeader.svelte';
import RemitoFiscalControls from '$lib/remitos/components/RemitoFiscalControls.svelte';
import RemitoItemsTable from '$lib/remitos/components/RemitoItemsTable.svelte';
import RemitoPhotoLightbox from '$lib/remitos/components/RemitoPhotoLightbox.svelte';
import RemitoQuickProductDialog from '$lib/remitos/components/RemitoQuickProductDialog.svelte';
import { RemitoDetailState } from '$lib/remitos/remito-detail-state.svelte';

const queryClient = useQueryClient();
const remitoId = $derived(Number(page.params.id));
const detailState = new RemitoDetailState();
let actionFeedback = $state<string | null>(null);

const remitoQuery = createQuery(() =>
	getRemitoApiV1RemitosIdGetOptions({
		path: { id: remitoId },
	}),
);

const productsQuery = createQuery(() =>
	productReadMultiApiV1ProductsGetOptions({
		query: { limit: 1000 },
	}),
);

const products = $derived.by<ProductResponse[]>(() => {
	const raw = productsQuery.data;
	if (Array.isArray(raw)) return raw as ProductResponse[];
	if (raw && 'data' in raw) return raw.data as ProductResponse[];
	return [];
});

$effect(() => {
	if (remitoQuery.data) {
		detailState.initFromRemito(remitoQuery.data as RemitoResponse);
	}
});

async function handleUpdateItem(
	itemId: number,
	updates: Record<string, unknown>,
): Promise<void> {
	await updateItemApiV1RemitosIdItemsItemIdPut({
		path: { id: remitoId, item_id: itemId },
		body: updates,
	});
	await queryClient.invalidateQueries({
		queryKey: ['getRemitoApiV1RemitosIdGet', { path: { id: remitoId } }],
	});
}

async function handleFiscalSplitChange(
	blanco: number,
	negro: number,
	iva: number,
): Promise<void> {
	await patchRemitoApiV1RemitosIdPatch({
		path: { id: remitoId },
		body: {
			fiscal_blanco_pct: blanco,
			fiscal_negro_pct: negro,
			iva_pct: iva,
		},
	});
	await queryClient.invalidateQueries({
		queryKey: ['getRemitoApiV1RemitosIdGet', { path: { id: remitoId } }],
	});
}

async function handleConfirm(): Promise<void> {
	if (!detailState.canConfirm) return;
	detailState.isConfirming = true;
	actionFeedback = null;

	try {
		await confirmApiV1RemitosIdConfirmPost({
			path: { id: remitoId },
		});
		actionFeedback = 'Stock confirmado e ingresado al inventario con éxito.';
		await Promise.all([
			queryClient.invalidateQueries({
				queryKey: ['getRemitoApiV1RemitosIdGet', { path: { id: remitoId } }],
			}),
			queryClient.invalidateQueries({
				queryKey: ['listRemitosApiV1RemitosGet'],
			}),
			queryClient.invalidateQueries({
				queryKey: ['productReadMultiApiV1ProductsGet'],
			}),
		]);
	} catch (err: unknown) {
		actionFeedback =
			err instanceof Error ? err.message : 'Error al confirmar el stock';
	} finally {
		detailState.isConfirming = false;
	}
}

async function handleReject(): Promise<void> {
	if (
		!confirm(
			'¿Estás seguro de que deseás descartar este remito? Esta acción es irreversible.',
		)
	)
		return;
	detailState.isRejecting = true;
	try {
		await rejectApiV1RemitosIdRejectPost({
			path: { id: remitoId },
		});
		await queryClient.invalidateQueries({
			queryKey: ['getRemitoApiV1RemitosIdGet', { path: { id: remitoId } }],
		});
	} finally {
		detailState.isRejecting = false;
	}
}

async function handleCreateProduct(data: {
	sku: string;
	name: string;
	unit_price: number;
	product_type: 'discrete' | 'bulk';
}): Promise<ProductResponse> {
	const res = await productCreateApiV1ProductsPost({
		body: data,
	});
	await queryClient.invalidateQueries({
		queryKey: ['productReadMultiApiV1ProductsGet'],
	});
	return res.data as ProductResponse;
}

async function handleLinkProduct(
	itemId: number,
	productId: number,
): Promise<void> {
	await handleUpdateItem(itemId, {
		product_id: productId,
		is_verified_by_user: true,
	});
}
</script>

<svelte:head>
	<title>Auditar Remito #{remitoId} | Vitalcer Admin</title>
</svelte:head>

<div class="space-y-4">
	<!-- Top Bar & Warning Gate -->
	<RemitoDetailHeader
		{remitoId}
		{detailState}
		{actionFeedback}
		onConfirm={handleConfirm}
		onReject={handleReject}
	/>

	{#if remitoQuery.isLoading}
		<Card class="p-12 text-center">
			<RefreshCw class="w-8 h-8 text-emerald-600 animate-spin mx-auto mb-3" />
			<div class="text-sm font-semibold text-gray-700">Cargando comprobante...</div>
		</Card>
	{:else if detailState.remito}
		<!-- Split Grid: Lightbox on Left / Items Table on Right -->
		<div class="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
			<!-- Left: Photo Lightbox -->
			<div class="lg:col-span-5 sticky top-20">
				<RemitoPhotoLightbox {detailState} />
			</div>

			<!-- Right: Items Audit Grid & Fiscal Sliders -->
			<div class="lg:col-span-7 space-y-4">
				<RemitoFiscalControls
					{detailState}
					onChangeSplit={handleFiscalSplitChange}
				/>

				<RemitoItemsTable
					{detailState}
					{products}
					onUpdateItem={handleUpdateItem}
				/>
			</div>
		</div>
	{/if}

	<!-- Quick Product Modal -->
	<RemitoQuickProductDialog
		{detailState}
		onCreateProduct={handleCreateProduct}
		onLinkProduct={handleLinkProduct}
	/>
</div>
