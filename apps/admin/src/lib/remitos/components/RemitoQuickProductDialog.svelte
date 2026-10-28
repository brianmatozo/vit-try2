<script lang="ts">
import type { ProductResponse } from '@vitalcer/api';
import { Button, Dialog, Input } from '@vitalcer/ui';
import { AlertCircle, Sparkles } from 'lucide-svelte';
import type { RemitoDetailState } from '../remito-detail-state.svelte';

type NewProductInput = {
	sku: string;
	name: string;
	unit_price: number;
	product_type: 'discrete' | 'bulk';
};

interface Props {
	detailState: RemitoDetailState;
	onCreateProduct: (data: NewProductInput) => Promise<ProductResponse>;
	onLinkProduct: (itemId: number, productId: number) => Promise<void>;
}

let { detailState, onCreateProduct, onLinkProduct }: Props = $props();

let sku = $state('');
let name = $state('');
let unitPrice = $state(1000);
let productType = $state<'discrete' | 'bulk'>('discrete');
let isSubmitting = $state(false);
let errorMessage = $state<string | null>(null);

function autoSku(text: string): string {
	const clean = text
		.normalize('NFD')
		.replace(/[\u0300-\u036f]/g, '')
		.toUpperCase()
		.replace(/[^A-Z0-9]+/g, '-')
		.replace(/^-+|-+$/g, '')
		.slice(0, 24);
	return clean || `SKU-${Date.now().toString().slice(-6)}`;
}

$effect(() => {
	const it = detailState.activeItemForProduct;
	if (it) {
		name = it.raw_description;
		sku = autoSku(it.raw_description);
		unitPrice = Math.max(Math.round(it.calculated_unit_cost * 1.5), 500);
		productType = it.target_unit_type === 'bulk_grams' ? 'bulk' : 'discrete';
		errorMessage = null;
	}
});

async function handleSubmit(e: SubmitEvent): Promise<void> {
	e.preventDefault();
	const item = detailState.activeItemForProduct;
	if (!item) return;

	isSubmitting = true;
	errorMessage = null;
	try {
		const newProd = await onCreateProduct({
			sku: sku.trim(),
			name: name.trim(),
			unit_price: Math.round(unitPrice),
			product_type: productType,
		});
		await onLinkProduct(item.id, newProd.id);
		detailState.closeQuickProduct();
	} catch (err: unknown) {
		errorMessage =
			err instanceof Error ? err.message : 'Error al crear el producto';
	} finally {
		isSubmitting = false;
	}
}
</script>

<Dialog
	bind:open={detailState.isQuickProductOpen}
	title="Crear Nuevo Producto en Catálogo"
	description="Registrá un nuevo artículo rápidamente y asocialo a esta línea de remito."
	position="center"
>
	<form id="quickProductForm" onsubmit={handleSubmit} class="space-y-3.5 text-xs">
		{#if errorMessage}
			<div class="p-2.5 rounded bg-rose-50 border border-rose-200 text-rose-800 flex items-center gap-2">
				<AlertCircle class="w-4 h-4 text-rose-600 shrink-0" />
				<span>{errorMessage}</span>
			</div>
		{/if}

		<div>
			<label for="qp-sku" class="block font-semibold text-gray-700 mb-1">Código SKU / PLU *</label>
			<Input id="qp-sku" bind:value={sku} required class="font-mono text-xs uppercase" />
		</div>

		<div>
			<label for="qp-name" class="block font-semibold text-gray-700 mb-1">Nombre del Producto *</label>
			<Input id="qp-name" bind:value={name} required class="text-xs" />
		</div>

		<div class="grid grid-cols-2 gap-3">
			<div>
				<label for="qp-type" class="block font-semibold text-gray-700 mb-1">
					Tipo de Producto *
				</label>
				<select
					id="qp-type"
					bind:value={productType}
					class="w-full h-9 rounded-md border border-gray-300 bg-white px-2 py-1 text-xs text-gray-900 shadow-xs focus:outline-none focus:border-emerald-600"
				>
					<option value="discrete">Unidad (Discreto)</option>
					<option value="bulk">Granel / Pesable</option>
				</select>
			</div>

			<div>
				<label for="qp-price" class="block font-semibold text-gray-700 mb-1">
					Precio Venta al Público ($ ARS) *
				</label>
				<Input
					id="qp-price"
					type="number"
					min="1"
					bind:value={unitPrice}
					required
					class="text-xs font-mono font-bold"
				/>
			</div>
		</div>

		<div class="p-2.5 rounded bg-emerald-50/70 border border-emerald-100 flex items-center gap-2 text-2xs text-emerald-900">
			<Sparkles class="w-3.5 h-3.5 text-emerald-600 shrink-0" />
			<span>Se creará el producto y se vinculará automáticamente para futuros remitos.</span>
		</div>
	</form>

	{#snippet footer()}
		<Button variant="outline" size="sm" type="button" onclick={() => detailState.closeQuickProduct()}>
			Cancelar
		</Button>
		<Button size="sm" type="submit" form="quickProductForm" disabled={isSubmitting} class="bg-emerald-600 hover:bg-emerald-700 text-white">
			{isSubmitting ? 'Creando...' : 'Crear y Vincular'}
		</Button>
	{/snippet}
</Dialog>
