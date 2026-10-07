<script lang="ts">
import {
	createMutation,
	createQuery,
	useQueryClient,
} from '@tanstack/svelte-query';
import {
	adjustStockMutation,
	type InventoryLedgerResponse,
	logMermaMutation,
	type ProductResponse,
	productReadMultiApiV1ProductsGetOptions,
	receiveStockMutation,
} from '@vitalcer/api';
import { formatWeight } from '@vitalcer/core';
import { Badge, Button, Card, Dialog, Input } from '@vitalcer/ui';
import {
	AlertCircle,
	CheckCircle2,
	Info,
	PackagePlus,
	Sliders,
	Trash2,
} from 'lucide-svelte';

const queryClient = useQueryClient();

// Load product catalog for dropdown selection
const productsQuery = createQuery(() =>
	productReadMultiApiV1ProductsGetOptions({
		query: { limit: 1000 },
	}),
);

const products = $derived<ProductResponse[]>(
	productsQuery.data && 'data' in productsQuery.data
		? (productsQuery.data.data as ProductResponse[])
		: Array.isArray(productsQuery.data)
			? (productsQuery.data as ProductResponse[])
			: [],
);

// Success message state
let successBanner = $state<{
	title: string;
	description: string;
	ledger?: InventoryLedgerResponse;
} | null>(null);

// Error message state
let errorMessage = $state<string | null>(null);

// --- Modal 1: Inbound Receiving ---
let isReceiveOpen = $state(false);
let receiveProductId = $state<number | ''>('');
let receiveQuantity = $state<number | ''>('');
let receiveReferenceId = $state('');
let receiveNotes = $state('');

const selectedReceiveProduct = $derived(
	products.find((p) => p.id === Number(receiveProductId)),
);

const receiveMutation = createMutation(() => receiveStockMutation());

async function handleReceiveSubmit(e: SubmitEvent) {
	e.preventDefault();
	errorMessage = null;
	if (!receiveProductId || !receiveQuantity || Number(receiveQuantity) <= 0) {
		errorMessage =
			'Debes seleccionar un producto e ingresar una cantidad mayor a cero.';
		return;
	}

	try {
		const res = await receiveMutation.mutateAsync({
			body: {
				product_id: Number(receiveProductId),
				quantity: Number(receiveQuantity),
				reference_id: receiveReferenceId.trim() || null,
				notes: receiveNotes.trim() || null,
			},
		});

		await queryClient.invalidateQueries();
		isReceiveOpen = false;
		successBanner = {
			title: 'Recepción registrada exitosamente',
			description: `Se ingresaron ${receiveQuantity} ${selectedReceiveProduct?.product_type === 'bulk' ? 'g' : 'unidades'} para "${selectedReceiveProduct?.name}".`,
			ledger: res,
		};

		// Reset fields
		receiveProductId = '';
		receiveQuantity = '';
		receiveReferenceId = '';
		receiveNotes = '';
	} catch (err: unknown) {
		errorMessage =
			err instanceof Error
				? err.message
				: 'Error al procesar la recepción de stock.';
	}
}

// --- Modal 2: Shrinkage / Merma ---
let isMermaOpen = $state(false);
let mermaProductId = $state<number | ''>('');
let mermaQuantity = $state<number | ''>('');
let mermaNotes = $state('');
let mermaReferenceId = $state('');

const selectedMermaProduct = $derived(
	products.find((p) => p.id === Number(mermaProductId)),
);

const mermaMutation = createMutation(() => logMermaMutation());

async function handleMermaSubmit(e: SubmitEvent) {
	e.preventDefault();
	errorMessage = null;
	if (
		!mermaProductId ||
		!mermaQuantity ||
		Number(mermaQuantity) <= 0 ||
		!mermaNotes.trim()
	) {
		errorMessage =
			'Debes especificar producto, cantidad mayor a 0 y el motivo obligatorio.';
		return;
	}

	try {
		const res = await mermaMutation.mutateAsync({
			body: {
				product_id: Number(mermaProductId),
				quantity: Number(mermaQuantity),
				notes: mermaNotes.trim(),
				reference_id: mermaReferenceId.trim() || null,
			},
		});

		await queryClient.invalidateQueries();
		isMermaOpen = false;
		successBanner = {
			title: 'Merma descontada de inventario',
			description: `Se dio de baja ${mermaQuantity} ${selectedMermaProduct?.product_type === 'bulk' ? 'g' : 'unidades'} de "${selectedMermaProduct?.name}".`,
			ledger: res,
		};

		// Reset fields
		mermaProductId = '';
		mermaQuantity = '';
		mermaNotes = '';
		mermaReferenceId = '';
	} catch (err: unknown) {
		errorMessage =
			err instanceof Error ? err.message : 'Error al asentar la merma.';
	}
}

// --- Modal 3: Manual Stock Reconciliation ---
let isAdjustOpen = $state(false);
let adjustProductId = $state<number | ''>('');
let adjustCountedStock = $state<number | ''>('');
let adjustNotes = $state('');
let adjustReferenceId = $state('');

const selectedAdjustProduct = $derived(
	products.find((p) => p.id === Number(adjustProductId)),
);

const calculatedAdjustmentDelta = $derived.by(() => {
	if (
		!selectedAdjustProduct ||
		adjustCountedStock === '' ||
		Number.isNaN(Number(adjustCountedStock))
	) {
		return null;
	}
	return Number(adjustCountedStock) - selectedAdjustProduct.current_stock;
});

const adjustMutation = createMutation(() => adjustStockMutation());

async function handleAdjustSubmit(e: SubmitEvent) {
	e.preventDefault();
	errorMessage = null;
	if (
		!adjustProductId ||
		adjustCountedStock === '' ||
		Number(adjustCountedStock) < 0 ||
		!adjustNotes.trim()
	) {
		errorMessage =
			'Debes ingresar el conteo físico (>= 0) y el motivo del ajuste.';
		return;
	}

	try {
		const res = await adjustMutation.mutateAsync({
			body: {
				product_id: Number(adjustProductId),
				counted_stock: Number(adjustCountedStock),
				notes: adjustNotes.trim(),
				reference_id: adjustReferenceId.trim() || null,
			},
		});

		await queryClient.invalidateQueries();
		isAdjustOpen = false;
		successBanner = {
			title: 'Ajuste de inventario aplicado',
			description: `Stock de "${selectedAdjustProduct?.name}" fijado en ${adjustCountedStock} (variación de ${res.quantity_delta}).`,
			ledger: res,
		};

		// Reset fields
		adjustProductId = '';
		adjustCountedStock = '';
		adjustNotes = '';
		adjustReferenceId = '';
	} catch (err: unknown) {
		errorMessage =
			err instanceof Error
				? err.message
				: 'Error al registrar el ajuste de stock.';
	}
}
</script>

<div class="space-y-4 sm:space-y-6 min-w-0">
  <!-- Title -->
  <div>
    <h1 class="text-lg sm:text-xl font-bold tracking-tight text-gray-900">Operaciones de Inventario</h1>
    <p class="text-xs text-gray-500 mt-0.5 sm:mt-1">
      Movimientos controlados por la lista general de stock
    </p>
  </div>

  <!-- Success Notification -->
  {#if successBanner}
    <Card class="p-3 sm:p-4 bg-emerald-50 border-emerald-200">
      <div class="flex items-start justify-between">
        <div class="flex items-start gap-2.5 sm:gap-3">
          <CheckCircle2 class="w-5 h-5 text-emerald-600 mt-0.5 shrink-0" />
          <div>
            <h3 class="text-sm font-semibold text-emerald-900">{successBanner.title}</h3>
            <p class="text-xs text-emerald-700 mt-0.5">{successBanner.description}</p>
            {#if successBanner.ledger}
              <p class="text-xs font-mono text-emerald-800 mt-1">
                Asiento Entrada #{successBanner.ledger.id} &bull; Δ: {successBanner.ledger.quantity_delta > 0 ? `+${successBanner.ledger.quantity_delta}` : successBanner.ledger.quantity_delta} &bull; Saldo posterior: {successBanner.ledger.balance_after}
              </p>
            {/if}
          </div>
        </div>
        <button
          type="button"
          onclick={() => (successBanner = null)}
          class="text-xs text-emerald-600 hover:text-emerald-800 cursor-pointer p-1"
        >
          Cerrar
        </button>
      </div>
    </Card>
  {/if}

  <!-- Error Notification -->
  {#if errorMessage}
    <Card class="p-3 sm:p-4 bg-rose-50 border-rose-200">
      <div class="flex items-start justify-between">
        <div class="flex items-start gap-2.5 sm:gap-3">
          <AlertCircle class="w-5 h-5 text-rose-600 mt-0.5 shrink-0" />
          <div>
            <h3 class="text-sm font-semibold text-rose-900">Error en la operación</h3>
            <p class="text-xs text-rose-700 mt-0.5">{errorMessage}</p>
          </div>
        </div>
        <button
          type="button"
          onclick={() => (errorMessage = null)}
          class="text-xs text-rose-600 hover:text-rose-800 cursor-pointer p-1"
        >
          Cerrar
        </button>
      </div>
    </Card>
  {/if}

  <!-- Action Cards Grid -->
  <div class="grid grid-cols-1 md:grid-cols-3 gap-3.5 sm:gap-6">
    <!-- 1. Stock Inbound / Receiving -->
    <Card class="p-4 sm:p-5 flex flex-col justify-between hover:border-gray-300 transition-colors">
      <div>
        <div class="w-9 h-9 rounded-md bg-emerald-100 text-emerald-700 flex items-center justify-center mb-3 sm:mb-4">
          <PackagePlus class="w-5 h-5" />
        </div>
        <h2 class="text-base font-semibold text-gray-900">Recepción de Proveedor</h2>
        <p class="text-xs text-gray-500 mt-1">
          Ingreso de mercadería por remito, factura de proveedor o reposición de bultos. Aumenta el stock físico disponible.
        </p>
      </div>

      <div class="mt-5 sm:mt-6 pt-3 sm:pt-4 border-t border-gray-100">
        <Button
          class="w-full justify-center h-10 sm:h-9"
          onclick={() => {
            errorMessage = null;
            isReceiveOpen = true;
          }}
        >
          Registrar Ingreso
        </Button>
      </div>
    </Card>

    <!-- 2. Shrinkage / Merma -->
    <Card class="p-4 sm:p-5 flex flex-col justify-between hover:border-gray-300 transition-colors">
      <div>
        <div class="w-9 h-9 rounded-md bg-rose-100 text-rose-700 flex items-center justify-center mb-3 sm:mb-4">
          <Trash2 class="w-5 h-5" />
        </div>
        <h2 class="text-base font-semibold text-gray-900">Merma / Pérdida</h2>
        <p class="text-xs text-gray-500 mt-1">
          Baja justificada por rotura, deshidratación natural en frutos secos/legumbres, vencimiento o degustación en local.
        </p>
      </div>

      <div class="mt-5 sm:mt-6 pt-3 sm:pt-4 border-t border-gray-100">
        <Button
          variant="outline"
          class="w-full justify-center text-rose-700 hover:bg-rose-50 hover:border-rose-300 h-10 sm:h-9"
          onclick={() => {
            errorMessage = null;
            isMermaOpen = true;
          }}
        >
          Registrar Merma
        </Button>
      </div>
    </Card>

    <!-- 3. Manual Audit Adjustment -->
    <Card class="p-4 sm:p-5 flex flex-col justify-between hover:border-gray-300 transition-colors">
      <div>
        <div class="w-9 h-9 rounded-md bg-amber-100 text-amber-700 flex items-center justify-center mb-3 sm:mb-4">
          <Sliders class="w-5 h-5" />
        </div>
        <h2 class="text-base font-semibold text-gray-900">Ajuste por Auditoría Física</h2>
        <p class="text-xs text-gray-500 mt-1">
          Conciliación de inventario ante recuentos. Registra el delta en lista general sin sobreescritura directa.
        </p>
      </div>

      <div class="mt-5 sm:mt-6 pt-3 sm:pt-4 border-t border-gray-100">
        <Button
          variant="outline"
          class="w-full justify-center text-amber-700 hover:bg-amber-50 hover:border-amber-300 h-10 sm:h-9"
          onclick={() => {
            errorMessage = null;
            isAdjustOpen = true;
          }}
        >
          Conciliar Stock
        </Button>
      </div>
    </Card>
  </div>
</div>

<!-- ================= Dialog 1: Inbound Receiving ================= -->
<Dialog
  bind:open={isReceiveOpen}
  title="Registrar Ingreso de Proveedor"
  description="Asienta una entrada de mercadería con su respectivo ticket o remito."
>
  {#snippet children()}
    <form id="receiveForm" onsubmit={handleReceiveSubmit} class="space-y-4">
      <div>
        <label for="receive-product" class="block text-xs font-semibold text-gray-700 mb-1">
          Artículo / Producto *
        </label>
        <select
          id="receive-product"
          bind:value={receiveProductId}
          required
          class="w-full h-10 sm:h-9 rounded-md border border-gray-300 bg-white px-3 py-1 text-base sm:text-sm text-gray-900 shadow-xs focus:outline-none focus:border-emerald-600 truncate"
        >
          <option value="" disabled>Selecciona un artículo...</option>
          {#each products as product (product.id)}
            <option value={product.id}>
              [{product.sku}] {product.name} ({product.product_type === 'bulk' ? 'Granel' : 'Unidades'}) - Stock: {product.current_stock}
            </option>
          {/each}
        </select>
      </div>

      {#if selectedReceiveProduct}
        <div class="p-2.5 bg-gray-50 rounded-md border border-gray-100 text-xs text-gray-600 flex justify-between">
          <span>Tipo: <strong class="capitalize">{selectedReceiveProduct.product_type}</strong></span>
          <span>Stock actual: <strong class="font-mono">{selectedReceiveProduct.current_stock}</strong></span>
        </div>
      {/if}

      <div>
        <label for="receive-qty" class="block text-xs font-semibold text-gray-700 mb-1">
          Cantidad a Ingresar ({selectedReceiveProduct?.product_type === 'bulk' ? 'Gramos' : 'Unidades'}) *
        </label>
        <Input
          id="receive-qty"
          type="number"
          min="1"
          placeholder="Ej: 5000 para 5kg o 24 para unidades"
          bind:value={receiveQuantity}
          required
        />
      </div>

      <div>
        <label for="receive-ref" class="block text-xs font-semibold text-gray-700 mb-1">
          N° Remito / Factura Proveedor
        </label>
        <Input
          id="receive-ref"
          placeholder="Ej: REM-0001-83921"
          bind:value={receiveReferenceId}
        />
      </div>

      <div>
        <label for="receive-notes" class="block text-xs font-semibold text-gray-700 mb-1">
          Observaciones / Proveedor
        </label>
        <Input
          id="receive-notes"
          placeholder="Ej: Distribuidora Juancito - Lote #442"
          bind:value={receiveNotes}
        />
      </div>
    </form>
  {/snippet}

  {#snippet footer()}
    <Button
      variant="outline"
      size="sm"
      type="button"
      class="flex-1 sm:flex-none justify-center"
      onclick={() => (isReceiveOpen = false)}
    >
      Cancelar
    </Button>
    <Button
      size="sm"
      type="submit"
      form="receiveForm"
      class="flex-1 sm:flex-none justify-center"
      disabled={receiveMutation.isPending}
    >
      {receiveMutation.isPending ? 'Guardando...' : 'Confirmar Ingreso'}
    </Button>
  {/snippet}
</Dialog>

<!-- ================= Dialog 2: Shrinkage / Merma ================= -->
<Dialog
  bind:open={isMermaOpen}
  title="Registrar Merma o Pérdida"
  description="Deduce stock físico por desperdicio, humedad o vencimiento."
>
  {#snippet children()}
    <form id="mermaForm" onsubmit={handleMermaSubmit} class="space-y-4">
      <div>
        <label for="merma-product" class="block text-xs font-semibold text-gray-700 mb-1">
          Artículo / Producto *
        </label>
        <select
          id="merma-product"
          bind:value={mermaProductId}
          required
          class="w-full h-10 sm:h-9 rounded-md border border-gray-300 bg-white px-3 py-1 text-base sm:text-sm text-gray-900 shadow-xs focus:outline-none focus:border-rose-600 truncate"
        >
          <option value="" disabled>Selecciona un artículo...</option>
          {#each products as product (product.id)}
            <option value={product.id}>
              [{product.sku}] {product.name} - Stock: {product.current_stock}
            </option>
          {/each}
        </select>
      </div>

      {#if selectedMermaProduct}
        <div class="p-2.5 bg-gray-50 rounded-md border border-gray-100 text-xs text-gray-600 flex justify-between">
          <span>Tipo: <strong class="capitalize">{selectedMermaProduct.product_type}</strong></span>
          <span>Stock actual: <strong class="font-mono">{selectedMermaProduct.current_stock}</strong></span>
        </div>
      {/if}

      <div>
        <label for="merma-qty" class="block text-xs font-semibold text-gray-700 mb-1">
          Cantidad a Deducir ({selectedMermaProduct?.product_type === 'bulk' ? 'Gramos' : 'Unidades'}) *
        </label>
        <Input
          id="merma-qty"
          type="number"
          min="1"
          placeholder="Ej: 150 para 150g o 2 para unidades rotas"
          bind:value={mermaQuantity}
          required
        />
      </div>

      <div>
        <label for="merma-notes" class="block text-xs font-semibold text-gray-700 mb-1">
          Motivo / Justificación Obligatoria *
        </label>
        <Input
          id="merma-notes"
          placeholder="Ej: Frasco roto en reposición / deshidratación tolva"
          bind:value={mermaNotes}
          required
        />
      </div>

      <div>
        <label for="merma-ref" class="block text-xs font-semibold text-gray-700 mb-1">
          Referencia de Turno / Incidente
        </label>
        <Input
          id="merma-ref"
          placeholder="Ej: INC-2026-03"
          bind:value={mermaReferenceId}
        />
      </div>
    </form>
  {/snippet}

  {#snippet footer()}
    <Button
      variant="outline"
      size="sm"
      type="button"
      class="flex-1 sm:flex-none justify-center"
      onclick={() => (isMermaOpen = false)}
    >
      Cancelar
    </Button>
    <Button
      size="sm"
      variant="destructive"
      type="submit"
      form="mermaForm"
      class="flex-1 sm:flex-none justify-center"
      disabled={mermaMutation.isPending}
    >
      {mermaMutation.isPending ? 'Guardando...' : 'Asentar Merma'}
    </Button>
  {/snippet}
</Dialog>

<!-- ================= Dialog 3: Audit Adjustment ================= -->
<Dialog
  bind:open={isAdjustOpen}
  title="Conciliación por Auditoría Física"
  description="Ajusta el saldo del sistema al conteo físico real de góndola."
>
  {#snippet children()}
    <form id="adjustForm" onsubmit={handleAdjustSubmit} class="space-y-4">
      <div>
        <label for="adjust-product" class="block text-xs font-semibold text-gray-700 mb-1">
          Artículo / Producto *
        </label>
        <select
          id="adjust-product"
          bind:value={adjustProductId}
          required
          class="w-full h-10 sm:h-9 rounded-md border border-gray-300 bg-white px-3 py-1 text-base sm:text-sm text-gray-900 shadow-xs focus:outline-none focus:border-amber-600 truncate"
        >
          <option value="" disabled>Selecciona un artículo...</option>
          {#each products as product (product.id)}
            <option value={product.id}>
              [{product.sku}] {product.name} - Stock Sist.: {product.current_stock}
            </option>
          {/each}
        </select>
      </div>

      {#if selectedAdjustProduct}
        <div class="p-2.5 bg-gray-50 rounded-md border border-gray-100 text-xs text-gray-600 flex justify-between">
          <span>Stock registrado en sistema:</span>
          <strong class="font-mono text-gray-900">
            {selectedAdjustProduct.product_type === 'bulk'
              ? formatWeight(selectedAdjustProduct.current_stock)
              : `${selectedAdjustProduct.current_stock} u`}
          </strong>
        </div>
      {/if}

      <div>
        <label for="adjust-counted" class="block text-xs font-semibold text-gray-700 mb-1">
          Conteo Físico Real en Góndola ({selectedAdjustProduct?.product_type === 'bulk' ? 'Gramos' : 'Unidades'}) *
        </label>
        <Input
          id="adjust-counted"
          type="number"
          min="0"
          placeholder="Conteo total presente en góndola"
          bind:value={adjustCountedStock}
          required
        />
      </div>

      {#if calculatedAdjustmentDelta !== null}
        <div class="p-2.5 rounded-md border text-xs flex items-center justify-between {calculatedAdjustmentDelta >= 0 ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-rose-50 border-rose-200 text-rose-800'}">
          <span>Variación a asentar en Ledger:</span>
          <strong class="font-mono font-bold">
            {calculatedAdjustmentDelta >= 0 ? `+${calculatedAdjustmentDelta}` : calculatedAdjustmentDelta}
          </strong>
        </div>
      {/if}

      <div>
        <label for="adjust-notes" class="block text-xs font-semibold text-gray-700 mb-1">
          Justificación Obligatoria del Ajuste *
        </label>
        <Input
          id="adjust-notes"
          placeholder="Ej: Recuento ciego mensual / Corrección por error de tipeo"
          bind:value={adjustNotes}
          required
        />
      </div>

      <div>
        <label for="adjust-ref" class="block text-xs font-semibold text-gray-700 mb-1">
          Código de Sesión de Auditoría
        </label>
        <Input
          id="adjust-ref"
          placeholder="Ej: AUDIT-2026-Q1"
          bind:value={adjustReferenceId}
        />
      </div>
    </form>
  {/snippet}

  {#snippet footer()}
    <Button
      variant="outline"
      size="sm"
      type="button"
      class="flex-1 sm:flex-none justify-center"
      onclick={() => (isAdjustOpen = false)}
    >
      Cancelar
    </Button>
    <Button
      size="sm"
      type="submit"
      form="adjustForm"
      class="flex-1 sm:flex-none justify-center"
      disabled={adjustMutation.isPending}
    >
      {adjustMutation.isPending ? 'Guardando...' : 'Aplicar Ajuste'}
    </Button>
  {/snippet}
</Dialog>
