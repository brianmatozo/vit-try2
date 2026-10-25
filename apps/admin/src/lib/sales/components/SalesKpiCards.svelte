<script lang="ts">
import { formatARS } from '@vitalcer/core';
import { Card } from '@vitalcer/ui';
import { DollarSign, Package, ShoppingBag, TrendingUp } from 'lucide-svelte';
import type { SalesKpiMetrics } from '../sales-metrics';

interface Props {
	kpis: SalesKpiMetrics;
}

let { kpis }: Props = $props();
</script>

<div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
	<!-- Total Facturado -->
	<Card class="p-4 sm:p-5 flex flex-col justify-between">
		<div class="flex items-center justify-between text-gray-500 mb-2">
			<span class="text-xs font-semibold uppercase tracking-wider">Total Facturado (Hoy)</span>
			<div class="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
				<DollarSign class="w-4 h-4" />
			</div>
		</div>
		<div>
			<div class="text-xl sm:text-2xl font-black text-emerald-700">
				{formatARS(kpis.totalRevenueToday)}
			</div>
			<div class="text-xs text-gray-400 mt-0.5">Monto cobrado hoy</div>
		</div>
	</Card>

	<!-- Cantidad de Tickets -->
	<Card class="p-4 sm:p-5 flex flex-col justify-between">
		<div class="flex items-center justify-between text-gray-500 mb-2">
			<span class="text-xs font-semibold uppercase tracking-wider">Tickets Emitidos (Hoy)</span>
			<div class="p-2 bg-blue-50 text-blue-600 rounded-lg">
				<ShoppingBag class="w-4 h-4" />
			</div>
		</div>
		<div>
			<div class="text-xl sm:text-2xl font-black text-gray-900">
				{kpis.todayTicketsCount}
			</div>
			<div class="text-xs text-gray-400 mt-0.5">Operaciones hoy ({kpis.totalTicketsCount} total)</div>
		</div>
	</Card>

	<!-- Ticket Promedio -->
	<Card class="p-4 sm:p-5 flex flex-col justify-between">
		<div class="flex items-center justify-between text-gray-500 mb-2">
			<span class="text-xs font-semibold uppercase tracking-wider">Ticket Promedio (Hoy)</span>
			<div class="p-2 bg-violet-50 text-violet-600 rounded-lg">
				<TrendingUp class="w-4 h-4" />
			</div>
		</div>
		<div>
			<div class="text-xl sm:text-2xl font-black text-gray-900">
				{formatARS(kpis.averageTicketToday)}
			</div>
			<div class="text-xs text-gray-400 mt-0.5">Promedio de hoy</div>
		</div>
	</Card>

	<!-- Artículos Vendidos -->
	<Card class="p-4 sm:p-5 flex flex-col justify-between">
		<div class="flex items-center justify-between text-gray-500 mb-2">
			<span class="text-xs font-semibold uppercase tracking-wider">Artículos Despachados (Hoy)</span>
			<div class="p-2 bg-amber-50 text-amber-600 rounded-lg">
				<Package class="w-4 h-4" />
			</div>
		</div>
		<div>
			<div class="text-xl sm:text-2xl font-black text-gray-900">
				{kpis.totalItemsSoldToday}
			</div>
			<div class="text-xs text-gray-400 mt-0.5">Líneas de venta hoy</div>
		</div>
	</Card>
</div>
