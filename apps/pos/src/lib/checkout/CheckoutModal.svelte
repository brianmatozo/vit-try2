<script lang="ts">
import { recordPosBatchSale } from '@vitalcer/api';
import { formatARS } from '@vitalcer/core';
import { Button, Dialog, Input } from '@vitalcer/ui';
import {
	AlertTriangle,
	ArrowRight,
	Banknote,
	CheckCircle2,
	CreditCard,
	Loader2,
	QrCode,
	Receipt,
} from 'lucide-svelte';
import { playError, playSuccess } from '../audio/sound';
import { type CartItem, cart } from '../cart/cart.svelte';

interface Props {
	open: boolean;
	oncomplete: () => void;
	oncancel: () => void;
}

let { open = $bindable(false), oncomplete, oncancel }: Props = $props();

type PaymentMethod = 'cash' | 'card' | 'qr';

let paymentMethod = $state<PaymentMethod>('cash');
let cashTendered = $state<number>(0);
let isProcessing = $state<boolean>(false);
let errorMessage = $state<string | null>(null);

// Success ticket summary
let completedTicket = $state<{
	ticketId: string;
	total: number;
	method: PaymentMethod;
	cashTendered?: number;
	change?: number;
	itemCount: number;
	timestamp: string;
} | null>(null);

const total = $derived(cart.totalAmount);

$effect(() => {
	if (open && !completedTicket) {
		paymentMethod = 'cash';
		cashTendered = cart.totalAmount;
		errorMessage = null;
	}
});

const change = $derived(cashTendered - total);
const isCashValid = $derived(paymentMethod !== 'cash' || cashTendered >= total);

function setCashAmount(amount: number) {
	cashTendered = amount;
}

function addCashAmount(bill: number) {
	if (cashTendered < total) {
		cashTendered = bill;
	} else {
		cashTendered += bill;
	}
}

async function handleConfirmSale() {
	if (cart.isEmpty) return;
	if (paymentMethod === 'cash' && cashTendered < total) {
		errorMessage =
			'El monto en efectivo ingresado es menor al total de la venta.';
		await playError();
		return;
	}

	isProcessing = true;
	errorMessage = null;

	const ticketId = `POS-${Date.now().toString().slice(-6)}`;
	const itemsToProcess = [...cart.items];

	try {
		// Deduct inventory for all cart items in a single atomic batch transaction
		const payloadItems = itemsToProcess.map((item) => ({
			product_id: item.product.id,
			quantity: item.isBulk ? (item.weightGrams ?? 1) : item.quantity,
		}));

		const response = await recordPosBatchSale({
			body: {
				ticket_reference_id: ticketId,
				items: payloadItems,
			},
		});

		if (response.error) {
			const errPayload = response.error as Record<string, unknown> | undefined;
			const detail =
				typeof errPayload?.detail === 'string'
					? errPayload.detail
					: 'Error procesando la venta';
			throw new Error(detail);
		}

		// Success!
		await playSuccess();

		completedTicket = {
			ticketId,
			total,
			method: paymentMethod,
			cashTendered: paymentMethod === 'cash' ? cashTendered : undefined,
			change: paymentMethod === 'cash' ? Math.max(0, change) : undefined,
			itemCount: cart.totalUnits,
			timestamp: new Date().toLocaleTimeString('es-AR', {
				hour: '2-digit',
				minute: '2-digit',
				second: '2-digit',
			}),
		};

		oncomplete();
	} catch (err: unknown) {
		const error = err as Error;
		console.error('POS Sale Error:', error);
		if (typeof navigator !== 'undefined' && !navigator.onLine) {
			errorMessage =
				'Sin conexión a internet: no se pudo registrar la venta en la base de datos.';
		} else {
			errorMessage =
				error.message || 'Error al registrar el cobro en el sistema.';
		}
		await playError();
	} finally {
		isProcessing = false;
	}
}

function handleStartNewSale() {
	completedTicket = null;
	open = false;
}

function handleClose() {
	if (isProcessing) return;
	completedTicket = null;
	open = false;
	oncancel();
}
</script>

<Dialog
	bind:open
	title={completedTicket ? 'Venta Finalizada' : 'Cobro de Caja'}
	description={completedTicket ? `Comprobante ${completedTicket.ticketId}` : `Total a cobrar: ${formatARS(total)}`}
	class="max-w-md"
>
	{#if completedTicket}
		<!-- Sale Completed Screen -->
		<div class="py-4 text-center space-y-4">
			<div class="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto ring-8 ring-emerald-50">
				<CheckCircle2 class="w-10 h-10" />
			</div>

			<div>
				<h3 class="text-xl font-black text-neutral-900">¡Cobro Registrado!</h3>
				<p class="text-xs text-neutral-500 mt-0.5">Stock descontado en el libro de inventario</p>
			</div>

			<!-- Ticket Card -->
			<div class="bg-neutral-50 border border-neutral-200 rounded-2xl p-4 text-left space-y-2.5">
				<div class="flex justify-between items-center text-xs text-neutral-500 pb-2 border-b border-neutral-200">
					<span>Ticket: <strong class="text-neutral-800">{completedTicket.ticketId}</strong></span>
					<span>{completedTicket.timestamp}</span>
				</div>

				<div class="flex justify-between items-center">
					<span class="text-sm font-semibold text-neutral-600">Total Cobrado</span>
					<span class="text-xl font-black text-emerald-600">{formatARS(completedTicket.total)}</span>
				</div>

				<div class="flex justify-between items-center text-xs text-neutral-600">
					<span>Medio de Pago</span>
					<span class="font-bold uppercase">
						{completedTicket.method === 'cash' ? 'Efectivo' : completedTicket.method === 'card' ? 'Tarjeta' : 'QR / Transf.'}
					</span>
				</div>

				{#if completedTicket.method === 'cash' && completedTicket.change !== undefined}
					<div class="pt-2 border-t border-neutral-200 flex justify-between items-center">
						<span class="text-sm font-bold text-neutral-700">Vuelto Entregado</span>
						<span class="text-lg font-black text-neutral-900">{formatARS(completedTicket.change)}</span>
					</div>
				{/if}
			</div>

			<Button
				variant="primary"
				onclick={handleStartNewSale}
				class="w-full h-13 text-base font-bold bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-lg shadow-emerald-600/20 flex items-center justify-center gap-2"
			>
				<span>Nueva Venta</span>
				<ArrowRight class="w-5 h-5" />
			</Button>
		</div>
	{:else}
		<!-- Payment Processing Screen -->
		<div class="space-y-4 pt-1">
			<!-- Big Total Header -->
			<div class="bg-neutral-900 text-white rounded-2xl p-4 text-center shadow-inner">
				<div class="text-xs font-semibold uppercase tracking-wider text-neutral-400">Total a Pagar</div>
				<div class="text-3xl font-black tracking-tight text-emerald-400 mt-1">
					{formatARS(total)}
				</div>
				<div class="text-xs text-neutral-400 mt-1">
					{cart.totalUnits} {cart.totalUnits === 1 ? 'artículo' : 'artículos'} en el carrito
				</div>
			</div>

			<!-- Payment Method Tabs -->
			<div class="grid grid-cols-3 gap-2">
				<button
					type="button"
					onclick={() => (paymentMethod = 'cash')}
					class="p-3 rounded-xl border flex flex-col items-center gap-1.5 transition active:scale-95 {paymentMethod === 'cash' ? 'bg-emerald-50 border-emerald-500 text-emerald-800 font-bold shadow-xs' : 'bg-white border-neutral-200 text-neutral-600 hover:bg-neutral-50'}"
				>
					<Banknote class="w-5 h-5 {paymentMethod === 'cash' ? 'text-emerald-600' : 'text-neutral-500'}" />
					<span class="text-xs">Efectivo</span>
				</button>

				<button
					type="button"
					onclick={() => (paymentMethod = 'card')}
					class="p-3 rounded-xl border flex flex-col items-center gap-1.5 transition active:scale-95 {paymentMethod === 'card' ? 'bg-emerald-50 border-emerald-500 text-emerald-800 font-bold shadow-xs' : 'bg-white border-neutral-200 text-neutral-600 hover:bg-neutral-50'}"
				>
					<CreditCard class="w-5 h-5 {paymentMethod === 'card' ? 'text-emerald-600' : 'text-neutral-500'}" />
					<span class="text-xs">Tarjeta</span>
				</button>

				<button
					type="button"
					onclick={() => (paymentMethod = 'qr')}
					class="p-3 rounded-xl border flex flex-col items-center gap-1.5 transition active:scale-95 {paymentMethod === 'qr' ? 'bg-emerald-50 border-emerald-500 text-emerald-800 font-bold shadow-xs' : 'bg-white border-neutral-200 text-neutral-600 hover:bg-neutral-50'}"
				>
					<QrCode class="w-5 h-5 {paymentMethod === 'qr' ? 'text-emerald-600' : 'text-neutral-500'}" />
					<span class="text-xs">QR / MP</span>
				</button>
			</div>

			<!-- Method Specific Forms -->
			{#if paymentMethod === 'cash'}
				<div class="space-y-3 p-3 bg-neutral-50 rounded-2xl border border-neutral-200">
					<div class="space-y-1">
						<label for="cash-received-input" class="block text-xs font-bold text-neutral-700">
							Dinero Recibido
						</label>
						<div class="relative">
							<span class="absolute left-3.5 top-1/2 -translate-y-1/2 text-lg font-bold text-neutral-400">$</span>
							<Input
								id="cash-received-input"
								type="number"
								min="0"
								step="100"
								bind:value={cashTendered}
								class="pl-8 text-xl font-black h-12 rounded-xl text-neutral-900"
							/>
						</div>
					</div>

					<!-- Bill Presets -->
					<div class="space-y-1">
						<div class="text-[11px] font-semibold text-neutral-500">Billetes frecuentes:</div>
						<div class="grid grid-cols-4 gap-1.5">
							<button
								type="button"
								onclick={() => setCashAmount(total)}
								class="py-2 px-1 bg-white hover:bg-neutral-100 active:scale-95 text-xs font-bold text-neutral-800 rounded-lg border border-neutral-200 shadow-2xs"
							>
								Exacto
							</button>
							<button
								type="button"
								onclick={() => addCashAmount(2000)}
								class="py-2 px-1 bg-white hover:bg-neutral-100 active:scale-95 text-xs font-bold text-neutral-800 rounded-lg border border-neutral-200 shadow-2xs"
							>
								+$2.000
							</button>
							<button
								type="button"
								onclick={() => addCashAmount(5000)}
								class="py-2 px-1 bg-white hover:bg-neutral-100 active:scale-95 text-xs font-bold text-neutral-800 rounded-lg border border-neutral-200 shadow-2xs"
							>
								+$5.000
							</button>
							<button
								type="button"
								onclick={() => addCashAmount(10000)}
								class="py-2 px-1 bg-white hover:bg-neutral-100 active:scale-95 text-xs font-bold text-neutral-800 rounded-lg border border-neutral-200 shadow-2xs"
							>
								+$10.000
							</button>
						</div>
					</div>

					<!-- Change / Vuelto Calculation -->
					{#if cashTendered >= total}
						<div class="p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between">
							<span class="text-xs font-bold text-emerald-900">Vuelto a Entregar:</span>
							<span class="text-xl font-black text-emerald-700">{formatARS(change)}</span>
						</div>
					{:else}
						<div class="p-2.5 bg-amber-50 border border-amber-200 rounded-xl flex items-center justify-between">
							<span class="text-xs font-bold text-amber-900">Faltante:</span>
							<span class="text-sm font-black text-amber-700">{formatARS(Math.abs(change))}</span>
						</div>
					{/if}
				</div>
			{:else if paymentMethod === 'card'}
				<div class="p-4 bg-neutral-50 rounded-2xl border border-neutral-200 text-center space-y-2">
					<CreditCard class="w-8 h-8 text-neutral-400 mx-auto" />
					<div class="text-sm font-bold text-neutral-800">Cobro con Terminal / Posnet</div>
					<p class="text-xs text-neutral-500">
						Pasá la tarjeta por la terminal externa por un monto de <strong class="text-neutral-900">{formatARS(total)}</strong>.
					</p>
				</div>
			{:else if paymentMethod === 'qr'}
				<div class="p-4 bg-neutral-50 rounded-2xl border border-neutral-200 text-center space-y-2">
					<QrCode class="w-8 h-8 text-neutral-400 mx-auto" />
					<div class="text-sm font-bold text-neutral-800">Cobro QR / Mercado Pago</div>
					<p class="text-xs text-neutral-500">
						El cliente debe transferir o escanear el QR del mostrador por <strong class="text-neutral-900">{formatARS(total)}</strong>.
					</p>
				</div>
			{/if}

			<!-- Error Alert -->
			{#if errorMessage}
				<div class="p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-2 text-rose-800 text-xs font-semibold">
					<AlertTriangle class="w-4 h-4 text-rose-600 shrink-0" />
					<span>{errorMessage}</span>
				</div>
			{/if}
		</div>
	{/if}

	{#snippet footer()}
		{#if !completedTicket}
			<Button
				variant="outline"
				onclick={handleClose}
				disabled={isProcessing}
				class="w-24 cursor-pointer"
			>
				Volver
			</Button>
			<Button
				variant="primary"
				onclick={handleConfirmSale}
				disabled={isProcessing || !isCashValid || cart.isEmpty}
				class="flex-1 h-12 text-sm font-bold bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-md flex items-center justify-center gap-2 cursor-pointer"
			>
				{#if isProcessing}
					<Loader2 class="w-4 h-4 animate-spin" />
					<span>Procesando...</span>
				{:else}
					<span>Confirmar Cobro ({formatARS(total)})</span>
				{/if}
			</Button>
		{/if}
	{/snippet}
</Dialog>
