<script lang="ts">
import { formatARS, formatWeight } from '@vitalcer/core';
import { Minus, Package, Plus, Scale, Trash2 } from 'lucide-svelte';
import type { CartItem } from '$lib/cart/cart.svelte';

interface Props {
	item: CartItem;
	onEditWeight: (item: CartItem) => void;
	onUpdateQuantity: (itemId: string, delta: number) => void;
	onRemove: (itemId: string) => void;
}

let { item, onEditWeight, onUpdateQuantity, onRemove }: Props = $props();
</script>

<div class="p-3 bg-neutral-900 rounded-2xl border border-neutral-800 shadow-sm space-y-2.5">
	<div class="flex items-start justify-between gap-2">
		<div class="min-w-0 flex-1">
			<div class="font-bold text-sm text-white truncate">
				{item.product.name}
			</div>
			<div class="flex items-center gap-1.5 mt-0.5 flex-wrap">
				{#if item.isBulk}
					<span class="inline-flex items-center gap-1 text-2xs font-bold px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
						<Scale class="w-3 h-3 text-amber-400" />
						PLU {item.product.plu_code || '-'}
					</span>
					<span class="text-xs text-neutral-400">
						{formatARS(item.unitPrice)} / {item.product.bulk_reference_grams || 100}g
					</span>
				{:else}
					<span class="inline-flex items-center gap-1 text-2xs font-medium px-1.5 py-0.5 rounded bg-neutral-800 text-neutral-400 border border-neutral-700">
						<Package class="w-3 h-3 text-neutral-500" />
						{item.product.sku}
					</span>
					<span class="text-xs text-neutral-400">
						{formatARS(item.unitPrice)} c/u
					</span>
				{/if}
			</div>
		</div>

		<!-- Line Total & Delete -->
		<div class="text-right shrink-0 flex items-center gap-2">
			<span class="text-base font-black text-emerald-400">
				{formatARS(item.lineTotal)}
			</span>
			<button
				type="button"
				onclick={() => onRemove(item.id)}
				class="w-8 h-8 rounded-xl bg-neutral-800 hover:bg-rose-950/60 hover:text-rose-400 border border-neutral-700/80 hover:border-rose-800/60 text-neutral-400 flex items-center justify-center transition active:scale-95"
				aria-label="Eliminar ítem"
			>
				<Trash2 class="w-4 h-4" />
			</button>
		</div>
	</div>

	<!-- Quantity or Weight Stepper Controls (Ergonomic: Subtotal on Left, Stepper on Right) -->
	<div class="pt-2 border-t border-neutral-800/80 flex items-center justify-between">
		<span class="text-xs font-semibold text-neutral-400">
			Subtotal: <span class="text-white font-bold">{formatARS(item.lineTotal)}</span>
		</span>

		{#if item.isBulk}
			<!-- Bulk Weight Modifier Button -->
			<button
				type="button"
				onclick={() => onEditWeight(item)}
				class="px-3 py-1.5 bg-neutral-800 hover:bg-neutral-700 active:scale-95 text-xs font-bold text-amber-300 rounded-xl border border-neutral-700 transition flex items-center gap-1.5"
			>
				<Scale class="w-3.5 h-3.5 text-amber-400" />
				<span>{formatWeight(item.weightGrams || 0)}</span>
				<span class="text-2xs text-neutral-400 font-normal">(Modificar)</span>
			</button>
		{:else}
			<!-- Discrete Unit Stepper on the RIGHT side -->
			<div class="flex items-center gap-1 bg-neutral-800 rounded-xl p-0.5 border border-neutral-700">
				<button
					type="button"
					onclick={() => onUpdateQuantity(item.id, -1)}
					class="w-8 h-8 rounded-lg bg-neutral-900 text-neutral-300 hover:text-white flex items-center justify-center transition active:scale-90"
					aria-label="Disminuir cantidad"
				>
					<Minus class="w-3.5 h-3.5" />
				</button>

				<span class="w-9 text-center text-sm font-extrabold text-white">
					{item.quantity}
				</span>

				<button
					type="button"
					onclick={() => onUpdateQuantity(item.id, 1)}
					class="w-8 h-8 rounded-lg bg-neutral-900 text-neutral-300 hover:text-white flex items-center justify-center transition active:scale-90"
					aria-label="Aumentar cantidad"
				>
					<Plus class="w-3.5 h-3.5" />
				</button>
			</div>
		{/if}
	</div>
</div>
