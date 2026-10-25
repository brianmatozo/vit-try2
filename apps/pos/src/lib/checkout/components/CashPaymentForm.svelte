<script lang="ts">
import { formatARS } from '@vitalcer/core';
import { Input } from '@vitalcer/ui';

interface Props {
	cashTendered: number;
	total: number;
	change: number;
	onSetCashAmount: (amount: number) => void;
	onAddCashAmount: (bill: number) => void;
}

let {
	cashTendered = $bindable(),
	total,
	change,
	onSetCashAmount,
	onAddCashAmount,
}: Props = $props();
</script>

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
		<div class="text-xs font-semibold text-neutral-500">Billetes frecuentes:</div>
		<div class="grid grid-cols-4 gap-1.5">
			<button
				type="button"
				onclick={() => onSetCashAmount(total)}
				class="py-2 px-1 bg-white hover:bg-neutral-100 active:scale-95 text-xs font-bold text-neutral-800 rounded-lg border border-neutral-200 shadow-2xs cursor-pointer"
			>
				Exacto
			</button>
			<button
				type="button"
				onclick={() => onAddCashAmount(2000)}
				class="py-2 px-1 bg-white hover:bg-neutral-100 active:scale-95 text-xs font-bold text-neutral-800 rounded-lg border border-neutral-200 shadow-2xs cursor-pointer"
			>
				+$2.000
			</button>
			<button
				type="button"
				onclick={() => onAddCashAmount(5000)}
				class="py-2 px-1 bg-white hover:bg-neutral-100 active:scale-95 text-xs font-bold text-neutral-800 rounded-lg border border-neutral-200 shadow-2xs cursor-pointer"
			>
				+$5.000
			</button>
			<button
				type="button"
				onclick={() => onAddCashAmount(10000)}
				class="py-2 px-1 bg-white hover:bg-neutral-100 active:scale-95 text-xs font-bold text-neutral-800 rounded-lg border border-neutral-200 shadow-2xs cursor-pointer"
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
