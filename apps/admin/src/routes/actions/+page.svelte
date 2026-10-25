<script lang="ts">
import {
	createMutation,
	createQuery,
	useQueryClient,
} from '@tanstack/svelte-query';
import {
	adjustStockMutation,
	logMermaMutation,
	type ProductResponse,
	productReadMultiApiV1ProductsGetOptions,
	receiveStockMutation,
} from '@vitalcer/api';
import { StockActionsState } from '$lib/actions/actions-state.svelte';
import ActionCards from '$lib/actions/components/ActionCards.svelte';
import ActionFeedbackBanners from '$lib/actions/components/ActionFeedbackBanners.svelte';
import AdjustmentDialog from '$lib/actions/components/AdjustmentDialog.svelte';
import MermaDialog from '$lib/actions/components/MermaDialog.svelte';
import ReceiveDialog from '$lib/actions/components/ReceiveDialog.svelte';

const queryClient = useQueryClient();
const state = new StockActionsState();

const productsQuery = createQuery(() =>
	productReadMultiApiV1ProductsGetOptions({
		query: { limit: 1000 },
	}),
);

$effect(() => {
	const raw = productsQuery.data;
	state.products =
		raw && 'data' in raw
			? (raw.data as ProductResponse[])
			: Array.isArray(raw)
				? (raw as ProductResponse[])
				: [];
});

const receiveMutation = createMutation(() => receiveStockMutation());
const mermaMutation = createMutation(() => logMermaMutation());
const adjustMutation = createMutation(() => adjustStockMutation());

async function handleReceiveSubmit(e: SubmitEvent) {
	e.preventDefault();
	if (!state.validateReceive()) return;
	try {
		const res = await receiveMutation.mutateAsync({
			body: state.buildReceivePayload(),
		});
		await queryClient.invalidateQueries();
		const qty = state.receiveQuantity;
		const name = state.selectedReceiveProduct?.name;
		const unit =
			state.selectedReceiveProduct?.product_type === 'bulk' ? 'g' : 'unidades';
		state.closeReceive();
		state.notifySuccess(
			'Recepción registrada exitosamente',
			`Se ingresaron ${qty} ${unit} para "${name}".`,
			res,
		);
		state.resetReceive();
	} catch (err: unknown) {
		state.notifyError(
			err instanceof Error
				? err.message
				: 'Error al procesar la recepción de stock.',
		);
	}
}

async function handleMermaSubmit(e: SubmitEvent) {
	e.preventDefault();
	if (!state.validateMerma()) return;
	try {
		const res = await mermaMutation.mutateAsync({
			body: state.buildMermaPayload(),
		});
		await queryClient.invalidateQueries();
		const qty = state.mermaQuantity;
		const name = state.selectedMermaProduct?.name;
		const unit =
			state.selectedMermaProduct?.product_type === 'bulk' ? 'g' : 'unidades';
		state.closeMerma();
		state.notifySuccess(
			'Merma descontada de inventario',
			`Se dio de baja ${qty} ${unit} de "${name}".`,
			res,
		);
		state.resetMerma();
	} catch (err: unknown) {
		state.notifyError(
			err instanceof Error ? err.message : 'Error al asentar la merma.',
		);
	}
}

async function handleAdjustSubmit(e: SubmitEvent) {
	e.preventDefault();
	if (!state.validateAdjust()) return;
	try {
		const res = await adjustMutation.mutateAsync({
			body: state.buildAdjustPayload(),
		});
		await queryClient.invalidateQueries();
		const counted = state.adjustCountedStock;
		const name = state.selectedAdjustProduct?.name;
		state.closeAdjust();
		state.notifySuccess(
			'Ajuste de inventario aplicado',
			`Stock de "${name}" fijado en ${counted} (variación de ${res.quantity_delta}).`,
			res,
		);
		state.resetAdjust();
	} catch (err: unknown) {
		state.notifyError(
			err instanceof Error
				? err.message
				: 'Error al registrar el ajuste de stock.',
		);
	}
}
</script>

<div class="space-y-4 sm:space-y-6 min-w-0">
  <div>
    <h1 class="text-lg sm:text-xl font-bold tracking-tight text-gray-900">Operaciones de Inventario</h1>
    <p class="text-xs text-gray-500 mt-0.5 sm:mt-1">
      Movimientos controlados por la lista general de stock
    </p>
  </div>

  <ActionFeedbackBanners
    successBanner={state.successBanner}
    errorMessage={state.errorMessage}
    onDismissSuccess={() => state.dismissSuccess()}
    onDismissError={() => state.dismissError()}
  />

  <ActionCards
    onOpenReceive={() => state.openReceive()}
    onOpenMerma={() => state.openMerma()}
    onOpenAdjust={() => state.openAdjust()}
  />

  <ReceiveDialog
    {state}
    isSubmitting={receiveMutation.isPending}
    onSubmit={handleReceiveSubmit}
  />

  <MermaDialog
    {state}
    isSubmitting={mermaMutation.isPending}
    onSubmit={handleMermaSubmit}
  />

  <AdjustmentDialog
    {state}
    isSubmitting={adjustMutation.isPending}
    onSubmit={handleAdjustSubmit}
  />
</div>
