<script lang="ts">
import type { FinancialClosureResponse } from '@vitalcer/api';
import { Card } from '@vitalcer/ui';
import {
	Banknote,
	CreditCard,
	DollarSign,
	QrCode,
	Scale,
	TrendingDown,
	TrendingUp,
	Wallet,
} from 'lucide-svelte';
import { formatClosureDateTime, formatCurrencyARS } from '../closure-filter.js';

interface Props {
	closure: FinancialClosureResponse;
}

let { closure }: Props = $props();

const expectedCash = $derived(
	closure.initial_cash +
		closure.cash_sales_amount +
		closure.cash_in_amount -
		closure.cash_out_amount,
);
</script>

<div class="space-y-4">
  <div class="bg-emerald-50/70 border border-emerald-200/80 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
    <div>
      <div class="text-xs font-semibold text-emerald-800 uppercase tracking-wide">
        Sesión de Caja Activa #{closure.id}
      </div>
      <div class="text-sm text-emerald-950 font-medium mt-0.5">
        Iniciada el {formatClosureDateTime(closure.opened_at)}
      </div>
    </div>
    <div class="flex items-center gap-4 text-xs text-emerald-900">
      <div>
        <span class="text-emerald-700">Tickets emitidos:</span>
        <strong class="ml-1 font-bold">{closure.sales_count}</strong>
      </div>
      <div>
        <span class="text-emerald-700">Fondo Inicial:</span>
        <strong class="ml-1 font-bold">{formatCurrencyARS(closure.initial_cash)}</strong>
      </div>
    </div>
  </div>

  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
    <Card class="p-4 border-gray-200 bg-white">
      <div class="flex items-center justify-between text-xs text-gray-500 mb-1">
        <span>Ventas Totales</span>
        <DollarSign class="size-4 text-emerald-600" />
      </div>
      <div class="text-2xl font-bold text-gray-900">
        {formatCurrencyARS(closure.total_sales_amount)}
      </div>
      <div class="text-xs text-gray-500 mt-2 space-y-0.5 pt-2 border-t border-gray-100">
        <div class="flex justify-between">
          <span class="flex items-center gap-1"><Banknote class="size-3 text-emerald-600" /> Efectivo</span>
          <span class="font-medium text-gray-800">{formatCurrencyARS(closure.cash_sales_amount)}</span>
        </div>
        <div class="flex justify-between">
          <span class="flex items-center gap-1"><CreditCard class="size-3 text-blue-600" /> Tarjeta</span>
          <span class="font-medium text-gray-800">{formatCurrencyARS(closure.card_sales_amount)}</span>
        </div>
        <div class="flex justify-between">
          <span class="flex items-center gap-1"><QrCode class="size-3 text-indigo-600" /> QR / Transf.</span>
          <span class="font-medium text-gray-800">{formatCurrencyARS(closure.qr_sales_amount)}</span>
        </div>
      </div>
    </Card>

    <Card class="p-4 border-gray-200 bg-white">
      <div class="flex items-center justify-between text-xs text-gray-500 mb-1">
        <span>Efectivo en Cajón Esperado</span>
        <Wallet class="size-4 text-emerald-600" />
      </div>
      <div class="text-2xl font-bold text-emerald-600">
        {formatCurrencyARS(expectedCash)}
      </div>
      <div class="text-xs text-gray-500 mt-2 space-y-0.5 pt-2 border-t border-gray-100">
        <div class="flex justify-between">
          <span>Fondo inicial:</span>
          <span class="font-medium">{formatCurrencyARS(closure.initial_cash)}</span>
        </div>
        <div class="flex justify-between">
          <span>+ Ventas efectivo:</span>
          <span class="font-medium">{formatCurrencyARS(closure.cash_sales_amount)}</span>
        </div>
        <div class="flex justify-between">
          <span>+ Neto movs:</span>
          <span class="font-medium">{formatCurrencyARS(closure.cash_in_amount - closure.cash_out_amount)}</span>
        </div>
      </div>
    </Card>

    <Card class="p-4 border-gray-200 bg-white">
      <div class="flex items-center justify-between text-xs text-gray-500 mb-1">
        <span>Movimientos de Cajón</span>
        <TrendingUp class="size-4 text-amber-600" />
      </div>
      <div class="text-2xl font-bold text-gray-900">
        {formatCurrencyARS(closure.cash_in_amount - closure.cash_out_amount)}
      </div>
      <div class="text-xs text-gray-500 mt-2 space-y-0.5 pt-2 border-t border-gray-100">
        <div class="flex justify-between text-emerald-700">
          <span class="flex items-center gap-1"><TrendingUp class="size-3" /> Ingresos extra:</span>
          <span class="font-medium">+{formatCurrencyARS(closure.cash_in_amount)}</span>
        </div>
        <div class="flex justify-between text-rose-700">
          <span class="flex items-center gap-1"><TrendingDown class="size-3" /> Gastos / Retiros:</span>
          <span class="font-medium">-{formatCurrencyARS(closure.cash_out_amount)}</span>
        </div>
      </div>
    </Card>

    <Card class="p-4 border-gray-200 bg-white">
      <div class="flex items-center justify-between text-xs text-gray-500 mb-1">
        <span>Merma Registrada Hoy</span>
        <Scale class="size-4 text-gray-400" />
      </div>
      <div class="text-2xl font-bold text-gray-700">
        {(closure.merma_total_grams / 1000).toFixed(2)} kg
      </div>
      <div class="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-100">
        <p class="leading-relaxed">
          Pérdidas de stock / mermas pesadas auditadas durante esta sesión.
        </p>
      </div>
    </Card>
  </div>
</div>
