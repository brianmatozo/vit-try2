<script lang="ts">
import { formatARS } from '@vitalcer/core';
import { Button, Dialog } from '@vitalcer/ui';
import { AlertTriangle, Loader2 } from 'lucide-svelte';
import { cart } from '../cart/cart.svelte';
import { CheckoutState } from './checkout-state.svelte';
import CashPaymentForm from './components/CashPaymentForm.svelte';
import CheckoutSuccessView from './components/CheckoutSuccessView.svelte';
import NonCashPaymentCard from './components/NonCashPaymentCard.svelte';
import PaymentMethodTabs from './components/PaymentMethodTabs.svelte';

interface Props {
	open: boolean;
	oncomplete: () => void;
	oncancel: () => void;
}

let { open = $bindable(false), oncomplete, oncancel }: Props = $props();

const state = new CheckoutState();

$effect(() => {
	if (open && !state.completedTicket) {
		state.initCash(cart.totalAmount);
	}
});

function handleClose() {
	if (state.isProcessing) return;
	state.reset();
	open = false;
	oncancel();
}

function handleStartNewSale() {
	state.reset();
	open = false;
}

async function handleConfirm() {
	await state.confirmSale(
		cart.items,
		cart.totalAmount,
		cart.totalUnits,
		oncomplete,
	);
}
</script>

<Dialog
	bind:open
	title={state.completedTicket ? 'Venta Finalizada' : 'Cobro de Caja'}
	description={state.completedTicket ? `Comprobante ${state.completedTicket.ticketId}` : `Total a cobrar: ${formatARS(cart.totalAmount)}`}
	class="max-w-md"
>
	{#if state.completedTicket}
		<CheckoutSuccessView
			ticket={state.completedTicket}
			onStartNewSale={handleStartNewSale}
		/>
	{:else}
		<div class="space-y-4 pt-1">
			<!-- Big Total Header -->
			<div class="bg-neutral-900 text-white rounded-2xl p-4 text-center shadow-inner">
				<div class="text-xs font-semibold uppercase tracking-wider text-neutral-400">Total a Pagar</div>
				<div class="text-3xl font-black tracking-tight text-emerald-400 mt-1">
					{formatARS(cart.totalAmount)}
				</div>
				<div class="text-xs text-neutral-400 mt-1">
					{cart.totalUnits} {cart.totalUnits === 1 ? 'artículo' : 'artículos'} en el carrito
				</div>
			</div>

			<!-- Payment Method Tabs -->
			<PaymentMethodTabs
				selectedMethod={state.paymentMethod}
				onSelectMethod={(method) => (state.paymentMethod = method)}
			/>

			<!-- Method Specific Views -->
			{#if state.paymentMethod === 'cash'}
				<CashPaymentForm
					bind:cashTendered={state.cashTendered}
					total={cart.totalAmount}
					change={state.getChange(cart.totalAmount)}
					onSetCashAmount={(amt) => state.setCashAmount(amt)}
					onAddCashAmount={(bill) => state.addCashAmount(bill, cart.totalAmount)}
				/>
			{:else}
				<NonCashPaymentCard
					method={state.paymentMethod}
					total={cart.totalAmount}
				/>
			{/if}

			<!-- Error Alert -->
			{#if state.errorMessage}
				<div class="p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-2 text-rose-800 text-xs font-semibold">
					<AlertTriangle class="w-4 h-4 text-rose-600 shrink-0" />
					<span>{state.errorMessage}</span>
				</div>
			{/if}
		</div>
	{/if}

	{#snippet footer()}
		{#if !state.completedTicket}
			<Button
				variant="outline"
				onclick={handleClose}
				disabled={state.isProcessing}
				class="w-24 cursor-pointer"
			>
				Volver
			</Button>
			<Button
				variant="primary"
				onclick={handleConfirm}
				disabled={state.isProcessing || !state.isCashValid(cart.totalAmount) || cart.isEmpty}
				class="flex-1 h-12 text-sm font-bold bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-md flex items-center justify-center gap-2 cursor-pointer"
			>
				{#if state.isProcessing}
					<Loader2 class="w-4 h-4 animate-spin" />
					<span>Procesando...</span>
				{:else}
					<span>Confirmar Cobro ({formatARS(cart.totalAmount)})</span>
				{/if}
			</Button>
		{/if}
	{/snippet}
</Dialog>
