<script lang="ts">
import { createQuery } from '@tanstack/svelte-query';
import {
	type ProductResponse,
	productReadMultiApiV1ProductsGetOptions,
} from '@vitalcer/api';
import { formatARS, formatWeight, parseBarcode } from '@vitalcer/core';
import { Badge, Button, Dialog, Input } from '@vitalcer/ui';
import { Package, Scale, Search, X } from 'lucide-svelte';

interface Props {
	open: boolean;
	onselect: (product: ProductResponse) => void;
	onclose: () => void;
}

let { open = $bindable(false), onselect, onclose }: Props = $props();

let searchTerm = $state('');
let filterType = $state<'all' | 'discrete' | 'bulk'>('all');

const productsQuery = createQuery(() =>
	productReadMultiApiV1ProductsGetOptions({
		query: { limit: 1000 },
	}),
);

const allProducts = $derived<ProductResponse[]>(
	productsQuery.data && 'data' in productsQuery.data
		? (productsQuery.data.data as ProductResponse[])
		: Array.isArray(productsQuery.data)
			? (productsQuery.data as ProductResponse[])
			: [],
);

const filteredProducts = $derived.by(() => {
	const rawTerm = searchTerm.trim();
	const term = rawTerm.toLowerCase();
	const parsed = parseBarcode(rawTerm);

	return allProducts.filter((p) => {
		if (p.is_active === false) return false;

		if (filterType === 'discrete' && p.product_type === 'bulk') return false;
		if (filterType === 'bulk' && p.product_type !== 'bulk') return false;

		if (!term) return true;

		// Match parsed scale PLU or discrete barcode directly
		if (parsed.isEmbeddedWeight && p.plu_code) {
			if (p.plu_code.toLowerCase() === parsed.skuOrPlu.toLowerCase()) {
				return true;
			}
		}

		const nameMatch = p.name.toLowerCase().includes(term);
		const skuMatch = p.sku.toLowerCase().includes(term);
		const pluMatch = p.plu_code
			? p.plu_code.toLowerCase().includes(term)
			: false;

		return nameMatch || skuMatch || pluMatch;
	});
});

function handleSelect(product: ProductResponse) {
	onselect(product);
	open = false;
	searchTerm = '';
}

function handleClose() {
	open = false;
	searchTerm = '';
	onclose();
}
</script>

<Dialog
	bind:open
	title="Buscar Producto"
	description="Catálogo por nombre, código de barras SKU o código PLU"
	class="max-w-md"
>
	<div class="space-y-3 pt-1">
		<!-- Search Input -->
		<div class="relative">
			<Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400 pointer-events-none" />
			<Input
				bind:value={searchTerm}
				placeholder="Escribí nombre, SKU o PLU..."
				class="pl-9 pr-9 h-11 text-base font-medium rounded-xl"
				autofocus
			/>
			{#if searchTerm}
				<button
					type="button"
					onclick={() => (searchTerm = '')}
					class="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 text-neutral-400 hover:text-neutral-600 rounded-full"
					aria-label="Borrar búsqueda"
				>
					<X class="w-4 h-4" />
				</button>
			{/if}
		</div>

		<!-- Filter Pills -->
		<div class="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
			<button
				type="button"
				onclick={() => (filterType = 'all')}
				class="px-3 py-1.5 rounded-full font-medium transition whitespace-nowrap {filterType === 'all' ? 'bg-neutral-900 text-white font-bold' : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200'}"
			>
				Todos ({allProducts.length})
			</button>
			<button
				type="button"
				onclick={() => (filterType = 'discrete')}
				class="px-3 py-1.5 rounded-full font-medium transition whitespace-nowrap {filterType === 'discrete' ? 'bg-neutral-900 text-white font-bold' : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200'}"
			>
				Unidades
			</button>
			<button
				type="button"
				onclick={() => (filterType = 'bulk')}
				class="px-3 py-1.5 rounded-full font-medium transition whitespace-nowrap {filterType === 'bulk' ? 'bg-neutral-900 text-white font-bold' : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200'}"
			>
				A Granel (Balanza)
			</button>
		</div>

		<!-- Results List -->
		<div class="space-y-1.5 max-h-[50dvh] overflow-y-auto pr-0.5">
			{#if productsQuery.isLoading}
				<div class="py-12 text-center text-sm text-neutral-500 font-medium">
					Cargando catálogo de productos...
				</div>
			{:else if filteredProducts.length === 0}
				<div class="py-12 text-center text-neutral-400">
					<p class="text-sm font-medium">No se encontraron productos</p>
					{#if searchTerm}
						<p class="text-xs text-neutral-400 mt-1">
							Verificá el texto o código buscado
						</p>
					{/if}
				</div>
			{:else}
				{#each filteredProducts as product (product.id)}
					<button
						type="button"
						onclick={() => handleSelect(product)}
						class="w-full text-left p-3 rounded-xl border border-neutral-100 hover:border-emerald-300 hover:bg-emerald-50/50 active:scale-[0.99] transition bg-white shadow-xs flex items-center justify-between gap-3 group cursor-pointer"
					>
						<div class="min-w-0 flex-1">
							<div class="font-bold text-sm text-neutral-900 group-hover:text-emerald-950 truncate">
								{product.name}
							</div>
							<div class="flex items-center gap-1.5 mt-1 flex-wrap">
								{#if product.product_type === 'bulk'}
									<span class="inline-flex items-center gap-1 text-[11px] px-1.5 py-0.5 rounded font-bold bg-amber-100 text-amber-900 border border-amber-200">
										<Scale class="w-3 h-3 text-amber-700" />
										PLU {product.plu_code || '-'}
									</span>
								{:else}
									<span class="inline-flex items-center gap-1 text-[11px] px-1.5 py-0.5 rounded font-medium bg-neutral-100 text-neutral-700">
										<Package class="w-3 h-3 text-neutral-500" />
										{product.sku}
									</span>
								{/if}

								<span class="text-[11px] text-neutral-400">
									Stock: {product.product_type === 'bulk' ? formatWeight(product.current_stock) : `${product.current_stock} un.`}
								</span>
							</div>
						</div>

						<div class="text-right shrink-0">
							<div class="text-base font-extrabold text-neutral-900 group-hover:text-emerald-700">
								{formatARS(product.unit_price)}
							</div>
							{#if product.product_type === 'bulk'}
								<div class="text-[11px] text-neutral-400 font-medium">
									/ {product.bulk_reference_grams || 100}g
								</div>
							{:else}
								<div class="text-[11px] text-neutral-400 font-medium">
									/ unidad
								</div>
							{/if}
						</div>
					</button>
				{/each}
			{/if}
		</div>
	</div>

	{#snippet footer()}
		<Button variant="outline" onclick={handleClose} class="w-full">
			Cerrar
		</Button>
	{/snippet}
</Dialog>
