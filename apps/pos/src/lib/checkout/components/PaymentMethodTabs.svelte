<script lang="ts">
import { Banknote, CreditCard, QrCode } from 'lucide-svelte';
import type { PaymentMethod } from '../checkout-state.svelte';

interface Props {
	selectedMethod: PaymentMethod;
	onSelectMethod: (method: PaymentMethod) => void;
}

let { selectedMethod, onSelectMethod }: Props = $props();
</script>

<div class="grid grid-cols-3 gap-2">
	<button
		type="button"
		onclick={() => onSelectMethod('cash')}
		class="p-3 rounded-xl border flex flex-col items-center gap-1.5 transition active:scale-95 cursor-pointer {selectedMethod === 'cash' ? 'bg-emerald-50 border-emerald-500 text-emerald-800 font-bold shadow-xs' : 'bg-white border-neutral-200 text-neutral-600 hover:bg-neutral-50'}"
	>
		<Banknote class="w-5 h-5 {selectedMethod === 'cash' ? 'text-emerald-600' : 'text-neutral-500'}" />
		<span class="text-xs">Efectivo</span>
	</button>

	<button
		type="button"
		onclick={() => onSelectMethod('card')}
		class="p-3 rounded-xl border flex flex-col items-center gap-1.5 transition active:scale-95 cursor-pointer {selectedMethod === 'card' ? 'bg-emerald-50 border-emerald-500 text-emerald-800 font-bold shadow-xs' : 'bg-white border-neutral-200 text-neutral-600 hover:bg-neutral-50'}"
	>
		<CreditCard class="w-5 h-5 {selectedMethod === 'card' ? 'text-emerald-600' : 'text-neutral-500'}" />
		<span class="text-xs">Tarjeta</span>
	</button>

	<button
		type="button"
		onclick={() => onSelectMethod('qr')}
		class="p-3 rounded-xl border flex flex-col items-center gap-1.5 transition active:scale-95 cursor-pointer {selectedMethod === 'qr' ? 'bg-emerald-50 border-emerald-500 text-emerald-800 font-bold shadow-xs' : 'bg-white border-neutral-200 text-neutral-600 hover:bg-neutral-50'}"
	>
		<QrCode class="w-5 h-5 {selectedMethod === 'qr' ? 'text-emerald-600' : 'text-neutral-500'}" />
		<span class="text-xs">QR / MP</span>
	</button>
</div>
