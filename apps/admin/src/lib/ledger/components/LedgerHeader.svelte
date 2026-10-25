<script lang="ts">
import { Button } from '@vitalcer/ui';
import { RefreshCw } from 'lucide-svelte';

interface Props {
	isFetching: boolean;
	onRefresh: () => void;
}

const { isFetching, onRefresh }: Props = $props();
</script>

<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
  <div>
    <h1 class="text-lg sm:text-xl font-bold tracking-tight text-gray-900">Historial y Auditoría de Stock</h1>
    <p class="text-xs text-gray-500 mt-0.5 sm:mt-1">
      Registro inmutable de movimientos, auditoría de balance y detección de desvíos.
    </p>
  </div>

  <div class="flex items-center gap-2 w-full sm:w-auto">
    <Button
      variant="outline"
      size="sm"
      class="w-full sm:w-auto justify-center"
      onclick={onRefresh}
      disabled={isFetching}
    >
      <RefreshCw class="w-3.5 h-3.5 {isFetching ? 'animate-spin' : ''}" />
      <span>Actualizar</span>
    </Button>
  </div>
</div>
