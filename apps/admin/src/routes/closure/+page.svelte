<script lang="ts">
import {
	createMutation,
	createQuery,
	useQueryClient,
} from '@tanstack/svelte-query';
import {
	closeClosureMutation,
	getActiveClosureOptions,
	listClosuresHistoryOptions,
	openClosureMutation,
	recordCashMovementMutation,
} from '@vitalcer/api';
import { AlertCircle, CheckCircle2, X } from 'lucide-svelte';
import { ClosureState } from '$lib/closure/closure-state.svelte';
import ActiveClosureView from '$lib/closure/components/ActiveClosureView.svelte';
import ArqueoClosureDialog from '$lib/closure/components/ArqueoClosureDialog.svelte';
import CashMovementDialog from '$lib/closure/components/CashMovementDialog.svelte';
import ClosureHeader from '$lib/closure/components/ClosureHeader.svelte';
import ClosureHistoryTable from '$lib/closure/components/ClosureHistoryTable.svelte';
import ClosureReceiptModal from '$lib/closure/components/ClosureReceiptModal.svelte';
import OpenClosureDialog from '$lib/closure/components/OpenClosureDialog.svelte';

const state = new ClosureState();
const queryClient = useQueryClient();

const activeClosureQuery = createQuery(() => ({
	...getActiveClosureOptions(),
	staleTime: 1000 * 15,
	refetchInterval: 1000 * 30,
}));

const historyQuery = createQuery(() => ({
	...listClosuresHistoryOptions({ query: { limit: 50 } }),
	staleTime: 1000 * 30,
}));

const openMutation = createMutation(() => openClosureMutation());
const movementMutation = createMutation(() => recordCashMovementMutation());
const closeMutation = createMutation(() => closeClosureMutation());

const activeClosure = $derived(
	activeClosureQuery.data?.closure ? activeClosureQuery.data.closure : null,
);

const expectedDrawerCash = $derived(
	activeClosure
		? activeClosure.initial_cash +
				activeClosure.cash_sales_amount +
				activeClosure.cash_in_amount -
				activeClosure.cash_out_amount
		: 0,
);

async function handleRefresh() {
	await Promise.all([activeClosureQuery.refetch(), historyQuery.refetch()]);
}

async function handleOpenConfirm(initialCash: number, notes?: string) {
	try {
		await openMutation.mutateAsync({
			body: {
				initial_cash: initialCash,
				notes: notes || undefined,
			},
		});
		await queryClient.invalidateQueries();
		state.closeOpenModal();
		state.showNotification('success', 'Sesión de caja abierta correctamente.');
	} catch (err: unknown) {
		const msg = err instanceof Error ? err.message : 'Error al abrir caja.';
		state.showNotification('error', msg);
	}
}

async function handleMovementConfirm(
	movementType: 'cash_in' | 'cash_out',
	amount: number,
	reason: string,
) {
	if (!activeClosure) return;
	try {
		await movementMutation.mutateAsync({
			path: { closure_id: activeClosure.id },
			body: {
				movement_type: movementType,
				amount,
				reason,
			},
		});
		await queryClient.invalidateQueries();
		state.closeMovementModal();
		state.showNotification(
			'success',
			movementType === 'cash_out'
				? 'Gasto de caja registrado.'
				: 'Ingreso extra registrado.',
		);
	} catch (err: unknown) {
		const msg =
			err instanceof Error ? err.message : 'Error registrando movimiento.';
		state.showNotification('error', msg);
	}
}

async function handleCloseConfirm(
	closureId: number,
	countedCash: number,
	breakdown: Record<number, number>,
	notes?: string,
) {
	try {
		const res = await closeMutation.mutateAsync({
			path: { closure_id: closureId },
			body: {
				counted_cash: countedCash,
				breakdown,
				notes: notes || undefined,
			},
		});
		await queryClient.invalidateQueries();
		state.closeArqueoModal();
		state.showNotification(
			'success',
			'Caja cerrada y arqueo conciliado exitosamente.',
		);
		if (res) {
			state.openReceipt(res);
		}
	} catch (err: unknown) {
		const msg = err instanceof Error ? err.message : 'Error al cerrar caja.';
		state.showNotification('error', msg);
	}
}
</script>

<div class="max-w-6xl mx-auto px-4 py-6 space-y-6">
  {#if state.notification}
    <div
      class="p-3 rounded-lg border flex items-center justify-between text-xs font-medium {state.notification.type === 'error' ? 'bg-rose-50 border-rose-200 text-rose-800' : 'bg-emerald-50 border-emerald-200 text-emerald-800'}"
    >
      <div class="flex items-center gap-2">
        {#if state.notification.type === 'error'}
          <AlertCircle class="size-4 shrink-0 text-rose-600" />
        {:else}
          <CheckCircle2 class="size-4 shrink-0 text-emerald-600" />
        {/if}
        <span>{state.notification.message}</span>
      </div>
      <button
        type="button"
        onclick={() => state.clearNotification()}
        class="text-gray-400 hover:text-gray-600"
      >
        <X class="size-3.5" />
      </button>
    </div>
  {/if}

  <ClosureHeader
    hasActiveClosure={!!activeClosure}
    activeStatus={activeClosure?.status}
    isRefreshing={activeClosureQuery.isFetching || historyQuery.isFetching}
    onOpenModal={() => state.openModal()}
    onMovementModal={() => state.openMovementModal()}
    onArqueoModal={() => state.openArqueoModal()}
    onRefresh={handleRefresh}
  />

  {#if activeClosure}
    <ActiveClosureView closure={activeClosure} />
  {/if}

  <ClosureHistoryTable
    closures={Array.isArray(historyQuery.data) ? historyQuery.data : []}
    isLoading={historyQuery.isLoading}
    onViewReceipt={(c) => state.openReceipt(c)}
  />

  <OpenClosureDialog
    bind:open={state.isOpenModalOpen}
    isSubmitting={openMutation.isPending}
    onClose={() => state.closeOpenModal()}
    onConfirm={handleOpenConfirm}
  />

  {#if activeClosure}
    <CashMovementDialog
      bind:open={state.isMovementModalOpen}
      closureId={activeClosure.id}
      isSubmitting={movementMutation.isPending}
      onClose={() => state.closeMovementModal()}
      onConfirm={handleMovementConfirm}
    />

    <ArqueoClosureDialog
      bind:open={state.isArqueoModalOpen}
      closureId={activeClosure.id}
      expectedCash={expectedDrawerCash}
      isSubmitting={closeMutation.isPending}
      onClose={() => state.closeArqueoModal()}
      onConfirm={handleCloseConfirm}
    />
  {/if}

  <ClosureReceiptModal
    bind:open={state.isReceiptModalOpen}
    closure={state.selectedReceiptClosure}
    onClose={() => state.closeReceipt()}
  />
</div>
