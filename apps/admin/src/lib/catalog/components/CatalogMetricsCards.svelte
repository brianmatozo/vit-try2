<script lang="ts">
import { Card } from '@vitalcer/ui';
import { AlertCircle, Layers, Scale } from 'lucide-svelte';
import type { CatalogMetricsData } from '../catalog-filter';

interface Props {
	metrics: CatalogMetricsData;
}

let { metrics }: Props = $props();
</script>

<div class="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-4">
  <Card class="p-2.5 sm:p-3">
    <div class="flex items-center justify-between">
      <span class="text-2xs sm:text-xs text-gray-500">Total Artículos</span>
      <Layers class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-gray-400" />
    </div>
    <p class="text-base sm:text-lg font-bold text-gray-900 font-mono mt-0.5 sm:mt-1">{metrics.total}</p>
  </Card>

  <Card class="p-2.5 sm:p-3">
    <div class="flex items-center justify-between">
      <span class="text-2xs sm:text-xs text-gray-500">Granel (Pesables)</span>
      <Scale class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-emerald-600" />
    </div>
    <p class="text-base sm:text-lg font-bold text-emerald-700 font-mono mt-0.5 sm:mt-1">{metrics.bulk}</p>
  </Card>

  <Card class="p-2.5 sm:p-3">
    <div class="flex items-center justify-between">
      <span class="text-2xs sm:text-xs text-gray-500">Unitarios</span>
      <Layers class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-blue-600" />
    </div>
    <p class="text-base sm:text-lg font-bold text-blue-700 font-mono mt-0.5 sm:mt-1">{metrics.discrete}</p>
  </Card>

  <Card class="p-2.5 sm:p-3">
    <div class="flex items-center justify-between">
      <span class="text-2xs sm:text-xs text-gray-500">Sin Stock</span>
      <AlertCircle class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-rose-500" />
    </div>
    <p class="text-base sm:text-lg font-bold text-rose-600 font-mono mt-0.5 sm:mt-1">{metrics.lowStock}</p>
  </Card>
</div>
