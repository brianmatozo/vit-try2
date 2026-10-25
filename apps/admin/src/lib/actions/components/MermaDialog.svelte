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
  bind:open={state.isMermaOpen}
  title="Registrar Merma o Pérdida"
  description="Deduce stock físico por desperdicio, humedad o vencimiento."
>
  <form id="mermaForm" onsubmit={onSubmit} class="space-y-4">
    <div>
      <label for="merma-product" class="block text-xs font-semibold text-gray-700 mb-1">
        Artículo / Producto *
      </label>
      <select
        id="merma-product"
        bind:value={state.mermaProductId}
        required
        class="w-full h-10 sm:h-9 rounded-md border border-gray-300 bg-white px-3 py-1 text-base sm:text-sm text-gray-900 shadow-xs focus:outline-none focus:border-rose-600 truncate"
      >
        <option value="" disabled>Selecciona un artículo...</option>
        {#each state.products as product (product.id)}
          <option value={product.id}>
            [{product.sku}] {product.name} - Stock: {product.current_stock}
          </option>
        {/each}
      </select>
    </div>

    {#if state.selectedMermaProduct}
      <div class="p-2.5 bg-gray-50 rounded-md border border-gray-100 text-xs text-gray-600 flex justify-between">
        <span>Tipo: <strong class="capitalize">{state.selectedMermaProduct.product_type}</strong></span>
        <span>Stock actual: <strong class="font-mono">{state.selectedMermaProduct.current_stock}</strong></span>
      </div>
    {/if}

    <div>
      <label for="merma-qty" class="block text-xs font-semibold text-gray-700 mb-1">
        Cantidad a Deducir ({state.selectedMermaProduct?.product_type === 'bulk' ? 'Gramos' : 'Unidades'}) *
      </label>
      <Input
        id="merma-qty"
        type="number"
        min="1"
        placeholder="Ej: 150 para 150g o 2 para unidades rotas"
        bind:value={state.mermaQuantity}
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
        bind:value={state.mermaNotes}
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
        bind:value={state.mermaReferenceId}
      />
    </div>
  </form>

  {#snippet footer()}
    <Button
      variant="outline"
      size="sm"
      type="button"
      class="flex-1 sm:flex-none justify-center"
      onclick={() => state.closeMerma()}
    >
      Cancelar
    </Button>
    <Button
      size="sm"
      variant="destructive"
      type="submit"
      form="mermaForm"
      class="flex-1 sm:flex-none justify-center"
      disabled={isSubmitting}
    >
      {isSubmitting ? 'Guardando...' : 'Asentar Merma'}
    </Button>
  {/snippet}
</Dialog>
