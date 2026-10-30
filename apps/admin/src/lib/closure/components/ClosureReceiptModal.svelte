<script lang="ts">
import type { FinancialClosureResponse } from '@vitalcer/api';
import { Button, Dialog } from '@vitalcer/ui';
import { Printer } from 'lucide-svelte';
import {
	formatClosureDateTime,
	formatCurrencyARS,
	getDiscrepancyBadgeInfo,
} from '../closure-filter.js';

interface Props {
	open: boolean;
	closure: FinancialClosureResponse | null;
	onClose: () => void;
}

let { open = $bindable(false), closure, onClose }: Props = $props();

function handlePrint() {
	window.print();
}
</script>

<Dialog
  bind:open
  centered
  title="Comprobante de Cierre de Caja"
  description="Resumen fiscal e imprimible para auditoría interna y archivo."
>
  {#if closure}
    {@const discrepancy = getDiscrepancyBadgeInfo(closure.expected_cash, closure.counted_cash)}
    <div id="printable-receipt" class="receipt-container bg-white border border-gray-200 rounded-lg p-4 font-mono text-xs text-gray-800 space-y-3">
      <div class="text-center border-b border-dashed border-gray-300 pb-2.5">
        <div class="font-bold text-sm tracking-tight">VITALCER DIETÉTICA</div>
        <div class="text-2xs text-gray-500">PLANILLA DE ARQUEO & CIERRE</div>
        <div class="text-2xs font-semibold text-gray-700 mt-1">SESIÓN #{closure.id} {closure.auto_closed ? '(AUTO-CIERRE)' : ''}</div>
      </div>

      <div class="space-y-1 text-2xs border-b border-dashed border-gray-300 pb-2">
        <div class="flex justify-between"><span class="text-gray-500">Apertura:</span><span>{formatClosureDateTime(closure.opened_at)}</span></div>
        <div class="flex justify-between"><span class="text-gray-500">Cierre:</span><span>{formatClosureDateTime(closure.closed_at)}</span></div>
      </div>

      <div class="space-y-1 text-2xs border-b border-dashed border-gray-300 pb-2">
        <div class="flex justify-between font-bold"><span>Fondo Inicial:</span><span>{formatCurrencyARS(closure.initial_cash)}</span></div>
        <div class="flex justify-between"><span>+ Ventas Efectivo:</span><span>{formatCurrencyARS(closure.cash_sales_amount)}</span></div>
        <div class="flex justify-between"><span>+ Ventas Tarjeta:</span><span>{formatCurrencyARS(closure.card_sales_amount)}</span></div>
        <div class="flex justify-between"><span>+ Ventas QR / MP:</span><span>{formatCurrencyARS(closure.qr_sales_amount)}</span></div>
        <div class="flex justify-between font-bold pt-1 border-t border-gray-200">
          <span>TOTAL VENTAS ({closure.sales_count} tkts):</span>
          <span>{formatCurrencyARS(closure.total_sales_amount)}</span>
        </div>
      </div>

      <div class="space-y-1 text-2xs border-b border-dashed border-gray-300 pb-2">
        <div class="flex justify-between text-emerald-800"><span>+ Ingresos extra:</span><span>+{formatCurrencyARS(closure.cash_in_amount)}</span></div>
        <div class="flex justify-between text-rose-800"><span>- Egresos / Gastos:</span><span>-{formatCurrencyARS(closure.cash_out_amount)}</span></div>
      </div>

      <div class="space-y-1 text-2xs border-b border-dashed border-gray-300 pb-2 bg-gray-50 p-2 rounded">
        <div class="flex justify-between"><span class="text-gray-600">Saldo Esperado Cajón:</span><span class="font-bold">{formatCurrencyARS(closure.expected_cash)}</span></div>
        <div class="flex justify-between"><span class="text-gray-600">Efectivo Recontado:</span><span class="font-bold text-gray-900">{closure.counted_cash !== null ? formatCurrencyARS(closure.counted_cash) : 'Sin Arqueo'}</span></div>
        <div class="flex justify-between font-bold text-xs pt-1 border-t border-gray-200">
          <span>Discrepancia:</span><span>{discrepancy.label}</span>
        </div>
      </div>

      {#if closure.notes}
        <div class="text-2xs text-gray-600 italic">Obs: {closure.notes}</div>
      {/if}

      <div class="pt-6 text-center text-2xs text-gray-400 border-t border-dashed border-gray-300 space-y-4">
        <div>_______________________________</div>
        <div>Firma y Aclaración del Cajero</div>
      </div>
    </div>
  {/if}

  {#snippet footer()}
    <div class="flex items-center w-full justify-between gap-2">
      <Button variant="outline" size="sm" onclick={onClose} class="mr-auto">Cerrar</Button>
      <Button variant="primary" size="sm" onclick={handlePrint}>
        <Printer class="size-4 mr-1.5" />
        Imprimir Comprobante (80mm)
      </Button>
    </div>
  {/snippet}
</Dialog>

<style>
  @media print {
    :global(body *) { visibility: hidden; }
    :global(#printable-receipt), :global(#printable-receipt *) { visibility: visible; }
    :global(#printable-receipt) {
      position: fixed;
      left: 0;
      top: 0;
      width: 80mm;
      margin: 0;
      padding: 4mm;
      border: none !important;
      font-size: 10pt;
    }
  }
</style>
