<script lang="ts">
import type { ProductResponse, RemitoItemResponse } from '@vitalcer/api';
import { formatARS } from '@vitalcer/core';
import { Trash2 } from 'lucide-svelte';
import ProductPickerCombobox from './ProductPickerCombobox.svelte';

type ItemUpdates = {
	effective_quantity?: number;
	multiplier?: number;
	product_id?: number;
	is_verified_by_user?: boolean;
};

interface Props {
	item: RemitoItemResponse;
	products: ProductResponse[];
	onUpdate: (itemId: number, updates: ItemUpdates) => Promise<void>;
	onCreateProduct: (item: RemitoItemResponse) => void;
}

let { item, products, onUpdate, onCreateProduct }: Props = $props();

const isExcluded = $derived(item.effective_quantity === 0);

const badge = $derived.by(() => {
	if (isExcluded)
		return { cls: 'bg-gray-100 text-gray-500', label: 'Excluido', icon: '⚪' };
	if (!item.product_id)
		return {
			cls: 'bg-rose-100 text-rose-800',
			label: 'Sin Vincular',
			icon: '🔴',
		};
	if (item.match_confidence >= 80 || item.is_verified_by_user) {
		return {
			cls: 'bg-emerald-100 text-emerald-800',
			label: 'Coincidencia',
			icon: '🟢',
		};
	}
	return { cls: 'bg-amber-100 text-amber-800', label: 'Revisar', icon: '🟡' };
});

function handleQtyChange(e: Event): void {
	const val = Number((e.target as HTMLInputElement).value);
	if (!Number.isNaN(val) && val >= 0)
		onUpdate(item.id, { effective_quantity: val });
}

function handleMultChange(e: Event): void {
	const val = Number((e.target as HTMLInputElement).value);
	if (!Number.isNaN(val) && val >= 1) onUpdate(item.id, { multiplier: val });
}
</script>

<tr class="hover:bg-gray-50/80 transition-colors {isExcluded ? 'opacity-50 bg-gray-50/50' : ''}">
	<!-- Status Badge & Line Index -->
	<td class="py-2.5 px-3 whitespace-nowrap">
		<span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-2xs font-semibold {badge.cls}">
			<span>{badge.icon}</span>
			<span>{badge.label}</span>
		</span>
	</td>

	<!-- Printed Description & Raw Cost -->
	<td class="col-raw-desc py-2.5 px-3">
		<div class="font-medium text-gray-900 text-xs leading-snug">
			{item.raw_description}
		</div>
		<div class="text-3xs text-gray-400 mt-0.5 font-mono">
			Impreso: {item.extracted_quantity} un. × {formatARS(item.extracted_unit_cost)} = {formatARS(item.extracted_line_total)}
		</div>
	</td>

	<!-- Product Match Combobox -->
	<td class="col-picker py-2.5 px-3">
		<ProductPickerCombobox
			selectedProductId={item.product_id}
			{products}
			onSelect={(p) => onUpdate(item.id, { product_id: p.id, is_verified_by_user: true })}
			onCreateNew={() => onCreateProduct(item)}
		/>
	</td>

	<!-- Multiplier (Pack units) -->
	<td class="py-2.5 px-3 text-center whitespace-nowrap">
		<div class="inline-flex items-center gap-1">
			<span class="text-3xs text-gray-400">×</span>
			<input
				type="number"
				min="1"
				value={item.multiplier}
				onchange={handleMultChange}
				disabled={isExcluded}
				class="w-14 h-7 text-center rounded border border-gray-300 text-xs font-semibold focus:outline-none focus:border-emerald-600 disabled:bg-gray-100"
			/>
		</div>
	</td>

	<!-- Effective Quantity Delivered -->
	<td class="py-2.5 px-3 text-center whitespace-nowrap">
		<input
			type="number"
			min="0"
			value={item.effective_quantity}
			onchange={handleQtyChange}
			class="w-14 h-7 text-center rounded border border-gray-300 text-xs font-bold focus:outline-none focus:border-emerald-600 {isExcluded ? 'text-gray-400 line-through' : 'text-gray-900'}"
		/>
	</td>

	<!-- Quantity to Commit -->
	<td class="py-2.5 px-3 text-right whitespace-nowrap font-mono font-semibold text-emerald-700 text-xs">
		{#if isExcluded}
			0
		{:else}
			+{item.quantity_to_commit} {item.target_unit_type === 'bulk_grams' ? 'g' : 'u'}
		{/if}
	</td>

	<!-- Calculated Net Unit Cost -->
	<td class="py-2.5 px-3 text-right whitespace-nowrap font-mono text-gray-900 font-bold text-xs">
		{#if isExcluded}
			$ 0
		{:else}
			{formatARS(item.calculated_unit_cost)}
		{/if}
	</td>

	<!-- Exclude / Zero Action -->
	<td class="py-2.5 px-3 text-right whitespace-nowrap">
		<button
			type="button"
			onclick={() => onUpdate(item.id, { effective_quantity: isExcluded ? item.extracted_quantity : 0 })}
			class="p-1 rounded text-gray-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
			title={isExcluded ? 'Restaurar ítem' : 'Excluir / Poner en 0'}
		>
			<Trash2 class="w-3.5 h-3.5" />
		</button>
	</td>
</tr>

<style>
	.col-raw-desc { min-width: 13rem; max-width: 16rem; }
	.col-picker { min-width: 14rem; }
</style>
