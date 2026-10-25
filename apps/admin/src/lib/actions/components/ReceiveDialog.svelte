<script lang="ts">
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
  bind:open={state.isReceiveOpen}
  title="Registrar Ingreso de Proveedor"
  description="Asienta una entrada de mercadería con su respectivo ticket o remito."
>
  <form id="receiveForm" onsubmit={onSubmit} class="space-y-4">
    <div>
      <label for="receive-product" class="block text-xs font-semibold text-gray-700 mb-1">
        Artículo / Producto *
      </label>
      <select
        id="receive-product"
        bind:value={state.receiveProductId}
        required
        class="w-full h-10 sm:h-9 rounded-md border border-gray-300 bg-white px-3 py-1 text-base sm:text-sm text-gray-900 shadow-xs focus:outline-none focus:border-emerald-600 truncate"
      >
        <option value="" disabled>Selecciona un artículo...</option>
        {#each state.products as product (product.id)}
          <option value={product.id}>
            [{product.sku}] {product.name} ({product.product_type === 'bulk' ? 'Granel' : 'Unidades'}) - Stock: {product.current_stock}
          </option>
        {/each}
      </select>
    </div>

    {#if state.selectedReceiveProduct}
      <div class="p-2.5 bg-gray-50 rounded-md border border-gray-100 text-xs text-gray-600 flex justify-between">
        <span>Tipo: <strong class="capitalize">{state.selectedReceiveProduct.product_type}</strong></span>
        <span>Stock actual: <strong class="font-mono">{state.selectedReceiveProduct.current_stock}</strong></span>
      </div>
    {/if}

    <div>
      <label for="receive-qty" class="block text-xs font-semibold text-gray-700 mb-1">
        Cantidad a Ingresar ({state.selectedReceiveProduct?.product_type === 'bulk' ? 'Gramos' : 'Unidades'}) *
      </label>
      <Input
        id="receive-qty"
        type="number"
        min="1"
        placeholder="Ej: 5000 para 5kg o 24 para unidades"
        bind:value={state.receiveQuantity}
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
        bind:value={state.receiveReferenceId}
      />
    </div>

    <div>
      <label for="receive-notes" class="block text-xs font-semibold text-gray-700 mb-1">
        Observaciones / Proveedor
      </label>
      <Input
        id="receive-notes"
        placeholder="Ej: Distribuidora Juancito - Lote #442"
        bind:value={state.receiveNotes}
      />
    </div>
  </form>

  {#snippet footer()}
    <Button
      variant="outline"
      size="sm"
      type="button"
      class="flex-1 sm:flex-none justify-center"
      onclick={() => state.closeReceive()}
    >
      Cancelar
    </Button>
    <Button
      size="sm"
      type="submit"
      form="receiveForm"
      class="flex-1 sm:flex-none justify-center"
      disabled={isSubmitting}
    >
      {isSubmitting ? 'Guardando...' : 'Confirmar Ingreso'}
    </Button>
  {/snippet}
</Dialog>
