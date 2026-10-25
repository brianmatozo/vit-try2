<script lang="ts">
import { Input } from '@vitalcer/ui';
import { Search } from 'lucide-svelte';

interface Props {
	searchTerm?: string;
	filteredCount: number;
	totalCount: number;
}

let { searchTerm = $bindable(''), filteredCount, totalCount }: Props = $props();
</script>

<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 sm:gap-3">
  <div class="relative w-full sm:max-w-sm">
    <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
    <Input
      type="search"
      placeholder="Buscar por PLU o nombre..."
      class="pl-8"
      bind:value={searchTerm}
    />
  </div>
  {#if searchTerm}
    <span class="text-xs text-gray-500 font-medium">
      Mostrando {filteredCount} de {totalCount} artículos
    </span>
  {/if}
</div>
