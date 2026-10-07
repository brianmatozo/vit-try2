<script lang="ts">
import type { ProductResponse } from '@vitalcer/api';
import {
	calculateBulkLineTotal,
	formatARS,
	formatWeight,
} from '@vitalcer/core';
import { Button, Dialog, Input } from '@vitalcer/ui';
import { Minus, Plus, Scale } from 'lucide-svelte';

interface Props {
	open: boolean;
	product: ProductResponse | null;
	initialWeight?: number;
	onconfirm: (weightGrams: number) => void;
	oncancel: () => void;
}

let {
	open = $bindable(false),
	product,
	initialWeight = 100,
	onconfirm,
	oncancel,
}: Props = $props();

let weightInput = $state<number>(100);

$effect(() => {
	if (open) {
		weightInput = initialWeight > 0 ? initialWeight : 100;
	}
});

let bulkRef = $derived(
	product?.bulk_reference_grams && product.bulk_reference_grams > 0
		? product.bulk_reference_grams
		: 100,
);

let computedTotal = $derived(
	product
		? calculateBulkLineTotal(
				product.unit_price,
				bulkRef,
				Math.max(1, weightInput || 1),
			)
		: 0,
);

function addWeight(delta: number) {
	weightInput = Math.max(1, (weightInput || 0) + delta);
}

function setWeight(val: number) {
	weightInput = Math.max(1, val);
}

function handleConfirm() {
	if (!product || weightInput <= 0) return;
	onconfirm(weightInput);
	open = false;
}

function handleClose() {
	open = false;
	oncancel();
}
</script>

<Dialog
	bind:open
	title="Ingresar Peso Balanza"
	description={product ? `${product.name} (PLU: ${product.plu_code || '-'})` : 'Pesar producto a granel'}
>
	{#if product}
		<div class="space-y-4 pt-1">
			<!-- Product Price Info Card -->
			<div class="p-3 bg-neutral-50 rounded-xl border border-neutral-200 flex items-center justify-between">
				<div>
					<div class="text-xs font-medium text-neutral-500">Precio de referencia</div>
					<div class="text-base font-bold text-neutral-900">
						{formatARS(product.unit_price)} <span class="text-xs font-normal text-neutral-500">/ {bulkRef}g</span>
					</div>
				</div>
				<div class="text-right">
					<div class="text-xs font-medium text-neutral-500">Subtotal calculado</div>
					<div class="text-lg font-black text-emerald-600">
						{formatARS(computedTotal)}
					</div>
				</div>
			</div>

			<!-- Weight Input Section -->
			<div class="space-y-2">
				<label for="weight-input" class="block text-sm font-semibold text-neutral-700">
					Peso en gramos (g)
				</label>
				<div class="flex items-center gap-2">
					<div class="relative flex-1">
						<Input
							id="weight-input"
							type="number"
							min="1"
							step="1"
							bind:value={weightInput}
							class="text-2xl font-bold tracking-tight text-center h-14 pr-10"
						/>
						<span class="absolute right-3.5 top-1/2 -translate-y-1/2 text-sm font-bold text-neutral-400">
							g
						</span>
					</div>
				</div>
				<div class="text-xs text-center text-neutral-500 font-medium">
					Equivalente a <span class="font-bold text-neutral-800">{formatWeight(weightInput || 0)}</span>
				</div>
			</div>

			<!-- Quick Weight Preset Buttons -->
			<div class="space-y-1.5">
				<div class="text-xs font-medium text-neutral-500">Valores rápidos:</div>
				<div class="grid grid-cols-4 gap-1.5">
					<button
						type="button"
						onclick={() => setWeight(100)}
						class="py-2.5 px-2 bg-neutral-100 hover:bg-neutral-200 active:scale-95 text-xs font-bold text-neutral-700 rounded-lg transition"
					>
						100 g
					</button>
					<button
						type="button"
						onclick={() => setWeight(250)}
						class="py-2.5 px-2 bg-neutral-100 hover:bg-neutral-200 active:scale-95 text-xs font-bold text-neutral-700 rounded-lg transition"
					>
						250 g
					</button>
					<button
						type="button"
						onclick={() => setWeight(500)}
						class="py-2.5 px-2 bg-neutral-100 hover:bg-neutral-200 active:scale-95 text-xs font-bold text-neutral-700 rounded-lg transition"
					>
						500 g
					</button>
					<button
						type="button"
						onclick={() => setWeight(1000)}
						class="py-2.5 px-2 bg-neutral-100 hover:bg-neutral-200 active:scale-95 text-xs font-bold text-neutral-700 rounded-lg transition"
					>
						1 kg
					</button>
				</div>

				<div class="grid grid-cols-4 gap-1.5 pt-1">
					<button
						type="button"
						onclick={() => addWeight(50)}
						class="py-2 px-1 bg-emerald-50 hover:bg-emerald-100 active:scale-95 text-xs font-semibold text-emerald-700 rounded-lg transition border border-emerald-200 flex items-center justify-center gap-1"
					>
						<Plus class="w-3 h-3" /> 50g
					</button>
					<button
						type="button"
						onclick={() => addWeight(100)}
						class="py-2 px-1 bg-emerald-50 hover:bg-emerald-100 active:scale-95 text-xs font-semibold text-emerald-700 rounded-lg transition border border-emerald-200 flex items-center justify-center gap-1"
					>
						<Plus class="w-3 h-3" /> 100g
					</button>
					<button
						type="button"
						onclick={() => addWeight(-50)}
						class="py-2 px-1 bg-rose-50 hover:bg-rose-100 active:scale-95 text-xs font-semibold text-rose-700 rounded-lg transition border border-rose-200 flex items-center justify-center gap-1"
					>
						<Minus class="w-3 h-3" /> 50g
					</button>
					<button
						type="button"
						onclick={() => addWeight(-100)}
						class="py-2 px-1 bg-rose-50 hover:bg-rose-100 active:scale-95 text-xs font-semibold text-rose-700 rounded-lg transition border border-rose-200 flex items-center justify-center gap-1"
					>
						<Minus class="w-3 h-3" /> 100g
					</button>
				</div>
			</div>
		</div>
	{/if}

	{#snippet footer()}
		<Button variant="outline" onclick={handleClose} class="w-24">
			Cancelar
		</Button>
		<Button
			variant="primary"
			onclick={handleConfirm}
			disabled={!product || weightInput <= 0}
			class="flex-1 bg-emerald-600 hover:bg-emerald-700 font-bold"
		>
			Confirmar ({formatARS(computedTotal)})
		</Button>
	{/snippet}
</Dialog>
