<script lang="ts">
import type { ProductResponse } from '@vitalcer/api';
import { Button, Input } from '@vitalcer/ui';
import { Check, ChevronDown, Plus, Search, X } from 'lucide-svelte';

interface Props {
	selectedProductId: number | null | undefined;
	products: ProductResponse[];
	onSelect: (product: ProductResponse) => void;
	onCreateNew?: () => void;
}

let { selectedProductId, products, onSelect, onCreateNew }: Props = $props();

let isOpen = $state(false);
let query = $state('');

const selectedProduct = $derived(
	selectedProductId ? products.find((p) => p.id === selectedProductId) : null,
);

const filteredProducts = $derived.by<ProductResponse[]>(() => {
	const q = query.trim().toLowerCase();
	if (!q) return products.slice(0, 30);
	return products
		.filter(
			(p) =>
				p.name.toLowerCase().includes(q) ||
				(p.sku?.toLowerCase().includes(q) ?? false),
		)
		.slice(0, 30);
});

function handlePick(p: ProductResponse): void {
	onSelect(p);
	isOpen = false;
	query = '';
}
</script>

<div class="relative w-full">
	<button
		type="button"
		onclick={() => (isOpen = !isOpen)}
		class="w-full text-left py-1.5 px-2 rounded border bg-white flex items-center justify-between text-xs transition-colors {selectedProduct ? 'border-gray-300 text-gray-900' : 'border-rose-300 bg-rose-50/30 text-rose-800'}"
	>
		<span class="truncate font-medium">
			{#if selectedProduct}
				{selectedProduct.name}
			{:else}
				<span class="text-rose-600 font-semibold italic">🔴 Seleccionar producto...</span>
			{/if}
		</span>
		<ChevronDown class="w-3.5 h-3.5 text-gray-400 shrink-0 ml-1" />
	</button>

	{#if isOpen}
		<!-- Backdrop for closing -->
		<button
			type="button"
			class="fixed inset-0 z-40 bg-transparent cursor-default"
			onclick={() => (isOpen = false)}
			aria-label="Cerrar selector"
		></button>

		<div class="absolute left-0 top-full mt-1 w-72 sm:w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50 p-2 space-y-1.5 text-xs">
			<div class="relative">
				<Search class="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
				<Input
					placeholder="Buscar por nombre o SKU..."
					bind:value={query}
					class="pl-8 py-1 h-8 text-xs"
					autofocus
				/>
				{#if query}
					<button
						type="button"
						onclick={() => (query = '')}
						class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
					>
						<X class="w-3 h-3" />
					</button>
				{/if}
			</div>

			{#if onCreateNew}
				<Button
					type="button"
					variant="outline"
					size="sm"
					onclick={() => {
						isOpen = false;
						onCreateNew();
					}}
					class="w-full justify-center gap-1.5 text-emerald-700 border-emerald-300 bg-emerald-50/50 hover:bg-emerald-100 py-1 h-7 text-2xs font-semibold"
				>
					<Plus class="w-3.5 h-3.5" />
					<span>Crear Nuevo Producto en Catálogo</span>
				</Button>
			{/if}

			<div class="max-h-48 overflow-y-auto space-y-0.5 pt-1 border-t border-gray-100">
				{#each filteredProducts as prod (prod.id)}
					{@const isSelected = prod.id === selectedProductId}
					<button
						type="button"
						onclick={() => handlePick(prod)}
						class="w-full text-left px-2 py-1.5 rounded flex items-center justify-between hover:bg-gray-100 transition-colors {isSelected ? 'bg-emerald-50 text-emerald-900 font-semibold' : 'text-gray-700'}"
					>
						<div class="truncate pr-2">
							<div class="truncate text-xs">{prod.name}</div>
							<div class="text-3xs text-gray-400 font-mono">{prod.sku}</div>
						</div>
						{#if isSelected}
							<Check class="w-3.5 h-3.5 text-emerald-600 shrink-0" />
						{/if}
					</button>
				{:else}
					<div class="p-3 text-center text-gray-400 text-2xs">
						No se encontraron productos coincidentes
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>
