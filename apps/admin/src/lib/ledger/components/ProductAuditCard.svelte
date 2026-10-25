<script lang="ts">
import type { StockAuditResponse } from '@vitalcer/api';
import { Button, Card } from '@vitalcer/ui';
import { AlertTriangle, ShieldCheck } from 'lucide-svelte';

interface Props {
	audit: StockAuditResponse;
	onClear: () => void;
}

const { audit, onClear }: Props = $props();
</script>

<Card class="p-3 sm:p-4 border-l-4 {audit.is_reconciled ? 'border-l-emerald-500 bg-emerald-50/30' : 'border-l-rose-500 bg-rose-50/30'}">
  <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 sm:gap-4">
    <div>
      <div class="flex items-center gap-2 flex-wrap">
        {#if audit.is_reconciled}
          <ShieldCheck class="w-4 h-4 sm:w-5 sm:h-5 text-emerald-600 shrink-0" />
          <span class="font-bold text-emerald-900 text-xs sm:text-sm">Stock Consistente</span>
        {:else}
          <AlertTriangle class="w-4 h-4 sm:w-5 sm:h-5 text-rose-600 shrink-0" />
          <span class="font-bold text-rose-900 text-xs sm:text-sm">¡Alerta de Desvío!</span>
        {/if}
        <span class="text-xs font-mono text-gray-600 font-medium">[{audit.sku}] {audit.name}</span>
      </div>

      <div class="mt-3 grid grid-cols-2 sm:flex sm:flex-wrap gap-2 sm:gap-x-6 sm:gap-y-1 text-xs text-gray-600 font-mono">
        <div class="bg-white/70 p-2 rounded sm:bg-transparent sm:p-0">
          Stock Físico: <strong class="text-gray-900">{audit.current_stock}</strong>
        </div>
        <div class="bg-white/70 p-2 rounded sm:bg-transparent sm:p-0">
          Suma Ledger: <strong class="text-gray-900">{audit.ledger_calculated_balance}</strong>
        </div>
        <div class="bg-white/70 p-2 rounded sm:bg-transparent sm:p-0">
          Reservado: <strong class="text-gray-900">{audit.reserved_stock}</strong>
        </div>
        <div class="bg-white/70 p-2 rounded sm:bg-transparent sm:p-0">
          Virtual Libre: <strong class="text-gray-900">{audit.virtual_stock}</strong>
        </div>
        <div class="bg-white/70 p-2 rounded sm:bg-transparent sm:p-0 col-span-2 sm:col-span-1">
          Desvío (Drift): <strong class={audit.drift === 0 ? 'text-emerald-700 font-bold' : 'text-rose-700 font-bold'}>{audit.drift}</strong>
        </div>
      </div>
    </div>

    <Button
      variant="outline"
      size="sm"
      class="w-full sm:w-auto text-xs justify-center shrink-0"
      onclick={onClear}
    >
      Limpiar Filtro
    </Button>
  </div>
</Card>
