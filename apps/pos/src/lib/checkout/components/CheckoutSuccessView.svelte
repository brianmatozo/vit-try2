<script lang="ts">
import { formatARS } from '@vitalcer/core';
import { Button } from '@vitalcer/ui';
import { ArrowRight, CheckCircle2 } from 'lucide-svelte';
import type { CompletedTicket } from '../checkout-state.svelte';

interface Props {
	ticket: CompletedTicket;
	onStartNewSale: () => void;
}

let { ticket, onStartNewSale }: Props = $props();
</script>

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
			<span>Ticket: <strong class="text-neutral-800">{ticket.ticketId}</strong></span>
			<span>{ticket.timestamp}</span>
		</div>

		<div class="flex justify-between items-center">
			<span class="text-sm font-semibold text-neutral-600">Total Cobrado</span>
			<span class="text-xl font-black text-emerald-600">{formatARS(ticket.total)}</span>
		</div>

		<div class="flex justify-between items-center text-xs text-neutral-600">
			<span>Medio de Pago</span>
			<span class="font-bold uppercase">
				{ticket.method === 'cash' ? 'Efectivo' : ticket.method === 'card' ? 'Tarjeta' : 'QR / Transf.'}
			</span>
		</div>

		{#if ticket.method === 'cash' && ticket.change !== undefined}
			<div class="pt-2 border-t border-neutral-200 flex justify-between items-center">
				<span class="text-sm font-bold text-neutral-700">Vuelto Entregado</span>
				<span class="text-lg font-black text-neutral-900">{formatARS(ticket.change)}</span>
			</div>
		{/if}
	</div>

	<Button
		variant="primary"
		onclick={onStartNewSale}
		class="w-full h-13 text-base font-bold bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-lg shadow-emerald-600/20 flex items-center justify-center gap-2 cursor-pointer"
	>
		<span>Nueva Venta</span>
		<ArrowRight class="w-5 h-5" />
	</Button>
</div>
