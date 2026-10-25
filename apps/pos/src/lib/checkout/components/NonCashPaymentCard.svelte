<script lang="ts">
import { formatARS } from '@vitalcer/core';
import { CreditCard, QrCode } from 'lucide-svelte';
import type { PaymentMethod } from '../checkout-state.svelte';

interface Props {
	method: PaymentMethod;
	total: number;
}

let { method, total }: Props = $props();
</script>

{#if method === 'card'}
	<div class="p-4 bg-neutral-50 rounded-2xl border border-neutral-200 text-center space-y-2">
		<CreditCard class="w-8 h-8 text-neutral-400 mx-auto" />
		<div class="text-sm font-bold text-neutral-800">Cobro con Terminal / Posnet</div>
		<p class="text-xs text-neutral-500">
			Pasá la tarjeta por la terminal externa por un monto de <strong class="text-neutral-900">{formatARS(total)}</strong>.
		</p>
	</div>
{:else if method === 'qr'}
	<div class="p-4 bg-neutral-50 rounded-2xl border border-neutral-200 text-center space-y-2">
		<QrCode class="w-8 h-8 text-neutral-400 mx-auto" />
		<div class="text-sm font-bold text-neutral-800">Cobro QR / Mercado Pago</div>
		<p class="text-xs text-neutral-500">
			El cliente debe transferir o escanear el QR del mostrador por <strong class="text-neutral-900">{formatARS(total)}</strong>.
		</p>
	</div>
{/if}
