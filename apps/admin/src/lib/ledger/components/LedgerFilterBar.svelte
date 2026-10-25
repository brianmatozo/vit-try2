<script lang="ts">
import { Button, Input } from '@vitalcer/ui';

interface Props {
	productIdInput: string;
	selectedMovementType: string;
	hasActiveFilters: boolean;
	recordCount: number;
	onReset: () => void;
}

let {
	productIdInput = $bindable(),
	selectedMovementType = $bindable(),
	hasActiveFilters,
	recordCount,
	onReset,
}: Props = $props();
</script>

<div class="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
  <div class="w-full sm:w-48">
    <Input
      type="number"
      placeholder="Filtrar por ID Prod..."
      bind:value={productIdInput}
    />
  </div>

  <div class="w-full sm:w-56">
    <select
      bind:value={selectedMovementType}
      class="w-full h-10 sm:h-9 rounded-md border border-gray-300 bg-white px-3 py-1 text-base sm:text-sm text-gray-800 shadow-xs focus:outline-none focus:border-emerald-600"
    >
      <option value="">Todos los movimientos</option>
      <option value="receiving">Entrada Proveedor</option>
      <option value="sale_pos">Venta Mostrador</option>
      <option value="delivery_fulfilled">Delivery</option>
      <option value="shrinkage_merma">Merma / Pérdida</option>
      <option value="manual_adjustment">Ajuste Manual</option>
    </select>
  </div>

  <div class="flex items-center justify-between w-full sm:w-auto sm:ml-auto gap-2 pt-1 sm:pt-0">
    {#if hasActiveFilters}
      <Button
        variant="ghost"
        size="sm"
        onclick={onReset}
      >
        Restablecer Filtros
      </Button>
    {/if}

    <span class="text-xs text-gray-500 font-mono ml-auto">
      {recordCount} movimientos
    </span>
  </div>
</div>
