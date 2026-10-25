<script lang="ts">
import { formatARS } from '@vitalcer/core';
import type { CartItem } from '$lib/cart/cart.svelte';
import CartItemCard from './CartItemCard.svelte';

interface Props {
	items: CartItem[];
	totalUnits: number;
	totalAmount: number;
	onEditWeight: (item: CartItem) => void;
	onUpdateQuantity: (itemId: string, delta: number) => void;
	onRemove: (itemId: string) => void;
}

let {
	items,
	totalUnits,
	totalAmount,
	onEditWeight,
	onUpdateQuantity,
	onRemove,
}: Props = $props();
</script>

<div class="space-y-2.5">
	<!-- Items Count & Cart Header -->
	<div class="flex items-center justify-between px-1 text-xs font-semibold text-neutral-400">
		<span>
			{items.length} {items.length === 1 ? 'ítem' : 'ítems'} ({totalUnits} {totalUnits === 1 ? 'unidad' : 'unidades'})
		</span>
		<span class="text-emerald-400 font-bold">Subtotal: {formatARS(totalAmount)}</span>
	</div>

	<!-- Cart Item Cards -->
	{#each items as item (item.id)}
		<CartItemCard
			{item}
			{onEditWeight}
			{onUpdateQuantity}
			{onRemove}
		/>
	{/each}
</div>
