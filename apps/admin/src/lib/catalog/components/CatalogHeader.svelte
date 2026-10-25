<script lang="ts">
import { Button } from '@vitalcer/ui';
import { Plus, RefreshCw } from 'lucide-svelte';

interface Props {
	isFetching: boolean;
	onNewProduct: () => void;
	onRefresh: () => void;
}

let { isFetching, onNewProduct, onRefresh }: Props = $props();
</script>

<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
  <div>
    <h1 class="text-lg sm:text-xl font-bold tracking-tight text-gray-900">Catálogo de Productos</h1>
    <p class="text-xs text-gray-500 mt-0.5 sm:mt-1">
      Consulta y administración de maestros de artículos, precios en ARS y sincronización de stock.
    </p>
  </div>

  <div class="flex items-center gap-2 w-full sm:w-auto">
    <Button
      variant="primary"
      size="sm"
      onclick={onNewProduct}
      class="flex-1 sm:flex-none justify-center"
    >
      <Plus class="w-3.5 h-3.5" />
      <span>Nuevo Producto</span>
    </Button>

    <Button
      variant="outline"
      size="sm"
      onclick={onRefresh}
      disabled={isFetching}
      class="flex-1 sm:flex-none justify-center"
    >
      <RefreshCw class="w-3.5 h-3.5 {isFetching ? 'animate-spin' : ''}" />
      <span>Actualizar</span>
    </Button>
  </div>
</div>
