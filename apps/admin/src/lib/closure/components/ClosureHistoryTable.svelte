<script lang="ts">
import type { FinancialClosureResponse } from '@vitalcer/api';
import { Badge, Button } from '@vitalcer/ui';
import { FileText, Inbox } from 'lucide-svelte';
import {
	formatClosureDateTime,
	formatCurrencyARS,
	getClosureStatusBadge,
	getDiscrepancyBadgeInfo,
} from '../closure-filter.js';

interface Props {
	closures: FinancialClosureResponse[];
	isLoading?: boolean;
	onViewReceipt: (closure: FinancialClosureResponse) => void;
}

let { closures, isLoading = false, onViewReceipt }: Props = $props();
</script>

<div class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-xs">
  <div class="p-4 border-b border-gray-200 flex items-center justify-between">
    <h3 class="text-sm font-bold text-gray-900">Historial de Turnos y Cierres</h3>
    <span class="text-xs text-gray-500">{closures.length} registros</span>
  </div>

  {#if isLoading}
    <div class="p-8 text-center text-xs text-gray-500">Cargando historial de cierres...</div>
  {:else if closures.length === 0}
    <div class="p-10 text-center flex flex-col items-center justify-center text-gray-400">
      <Inbox class="size-8 mb-2 stroke-1" />
      <p class="text-xs font-medium text-gray-500">No hay cierres de caja registrados</p>
    </div>
  {:else}
    <div class="overflow-x-auto">
      <table class="w-full text-left text-xs text-gray-600">
        <thead class="bg-gray-50 border-b border-gray-200 text-2xs uppercase tracking-wider text-gray-500">
          <tr>
            <th class="px-3.5 py-2.5 font-semibold">Sesión</th>
            <th class="px-3.5 py-2.5 font-semibold">Apertura / Cierre</th>
            <th class="px-3.5 py-2.5 font-semibold">Fondo Inicial</th>
            <th class="px-3.5 py-2.5 font-semibold">Total Ventas</th>
            <th class="px-3.5 py-2.5 font-semibold">Efectivo Recontado</th>
            <th class="px-3.5 py-2.5 font-semibold">Discrepancia</th>
            <th class="px-3.5 py-2.5 font-semibold">Estado</th>
            <th class="px-3.5 py-2.5 text-right font-semibold">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          {#each closures as c (c.id)}
            {@const statusBadge = getClosureStatusBadge(c.status, c.auto_closed)}
            {@const discrepancyBadge = getDiscrepancyBadgeInfo(c.expected_cash, c.counted_cash)}
            <tr class="hover:bg-gray-50/80 transition-colors">
              <td class="px-3.5 py-2.5 font-bold text-gray-900">#{c.id}</td>
              <td class="px-3.5 py-2.5 space-y-0.5">
                <div class="text-gray-800 font-medium">{formatClosureDateTime(c.opened_at)}</div>
                <div class="text-2xs text-gray-400">{c.closed_at ? formatClosureDateTime(c.closed_at) : 'En curso'}</div>
              </td>
              <td class="px-3.5 py-2.5 font-medium text-gray-800">{formatCurrencyARS(c.initial_cash)}</td>
              <td class="px-3.5 py-2.5 font-bold text-emerald-700">{formatCurrencyARS(c.total_sales_amount)}</td>
              <td class="px-3.5 py-2.5 font-medium text-gray-800">{c.counted_cash !== null ? formatCurrencyARS(c.counted_cash) : '—'}</td>
              <td class="px-3.5 py-2.5">
                <Badge variant={discrepancyBadge.variant}>{discrepancyBadge.label}</Badge>
              </td>
              <td class="px-3.5 py-2.5">
                <Badge variant={statusBadge.variant}>{statusBadge.label}</Badge>
              </td>
              <td class="px-3.5 py-2.5 text-right">
                <Button
                  variant="outline"
                  size="sm"
                  onclick={() => onViewReceipt(c)}
                  class="h-7 px-2 text-2xs"
                >
                  <FileText class="size-3.5 mr-1" />
                  Comprobante
                </Button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
