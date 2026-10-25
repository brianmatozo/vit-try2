<script lang="ts">
import { formatWeight } from '@vitalcer/core';
import { Button, Dialog, Input } from '@vitalcer/ui';
import type { StockActionsState } from '../actions-state.svelte';

interface Props {
	state: StockActionsState;
	isSubmitting: boolean;
	onSubmit: (e: SubmitEvent) => void;
}

let { state, isSubmitting, onSubmit }: Props = $props();
</script>

<Dialog
  bind:open={state.isAdjustOpen}
  title="Conciliación por Auditoría Física"
  description="Ajusta el saldo del sistema al conteo físico real de góndola."
>
  <form id="adjustForm" onsubmit={onSubmit} class="space-y-4">
    <div>
      <label for="adjust-product" class="block text-xs font-semibold text-gray-700 mb-1">
        Artículo / Producto *
      </label>
      <select
        id="adjust-product"
        bind:value={state.adjustProductId}
        required
        class="w-full h-10 sm:h-9 rounded-md border border-gray-300 bg-white px-3 py-1 text-base sm:text-sm text-gray-900 shadow-xs focus:outline-none focus:border-amber-600 truncate"
      >
        <option value="" disabled>Selecciona un artículo...</option>
        {#each state.products as product (product.id)}
          <option value={product.id}>
            [{product.sku}] {product.name} - Stock Sist.: {product.current_stock}
          </option>
        {/each}
      </select>
    </div>

    {#if state.selectedAdjustProduct}
      <div class="p-2.5 bg-gray-50 rounded-md border border-gray-100 text-xs text-gray-600 flex justify-between">
        <span>Stock registrado en sistema:</span>
        <strong class="font-mono text-gray-900">
          {state.selectedAdjustProduct.product_type === 'bulk'
            ? formatWeight(state.selectedAdjustProduct.current_stock)
            : `${state.selectedAdjustProduct.current_stock} u`}
        </strong>
      </div>
    {/if}

    <div>
      <label for="adjust-counted" class="block text-xs font-semibold text-gray-700 mb-1">
        Conteo Físico Real en Góndola ({state.selectedAdjustProduct?.product_type === 'bulk' ? 'Gramos' : 'Unidades'}) *
      </label>
      <Input
        id="adjust-counted"
        type="number"
        min="0"
        placeholder="Conteo total presente en góndola"
        bind:value={state.adjustCountedStock}
        required
      />
    </div>

    {#if state.calculatedAdjustmentDelta !== null}
      <div class="p-2.5 rounded-md border text-xs flex items-center justify-between {state.calculatedAdjustmentDelta >= 0 ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-rose-50 border-rose-200 text-rose-800'}">
        <span>Variación a asentar en Ledger:</span>
        <strong class="font-mono font-bold">
          {state.calculatedAdjustmentDelta >= 0 ? `+${state.calculatedAdjustmentDelta}` : state.calculatedAdjustmentDelta}
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
        bind:value={state.adjustNotes}
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
        bind:value={state.adjustReferenceId}
      />
    </div>
  </form>

  {#snippet footer()}
    <Button
      variant="outline"
      size="sm"
      type="button"
      class="flex-1 sm:flex-none justify-center"
      onclick={() => state.closeAdjust()}
    >
      Cancelar
    </Button>
    <Button
      size="sm"
      type="submit"
      form="adjustForm"
      class="flex-1 sm:flex-none justify-center"
      disabled={isSubmitting}
    >
      {isSubmitting ? 'Guardando...' : 'Aplicar Ajuste'}
    </Button>
  {/snippet}
</Dialog>
