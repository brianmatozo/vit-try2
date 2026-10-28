<script lang="ts">
import { formatARS } from '@vitalcer/core';
import { Card } from '@vitalcer/ui';
import { AlertCircle, CheckCircle2, TrendingUp } from 'lucide-svelte';
import type { RemitoKpis } from '../remitos-state.svelte';

interface Props {
	kpis: RemitoKpis;
}

let { kpis }: Props = $props();
</script>

<div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
	<!-- Staged / Pending -->
	<Card class="p-4 border-l-4 border-l-amber-500 flex items-center justify-between">
		<div>
			<div class="text-2xs font-semibold text-gray-400 uppercase tracking-wider">
				Pendientes de Revisión
			</div>
			<div class="text-2xl font-bold text-gray-900 mt-1">
				{kpis.stagedCount}
			</div>
			<div class="text-2xs text-amber-700 font-medium mt-0.5">
				{kpis.stagedCount === 1 ? '1 remito para auditar' : `${kpis.stagedCount} remitos para auditar`}
			</div>
		</div>
		<div class="w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center text-amber-600 shrink-0">
			<AlertCircle class="w-5 h-5" />
		</div>
	</Card>

	<!-- Committed -->
	<Card class="p-4 border-l-4 border-l-emerald-500 flex items-center justify-between">
		<div>
			<div class="text-2xs font-semibold text-gray-400 uppercase tracking-wider">
				Remitos Confirmados
			</div>
			<div class="text-2xl font-bold text-gray-900 mt-1">
				{kpis.committedCount}
			</div>
			<div class="text-2xs text-emerald-700 font-medium mt-0.5">
				Stock imputado al inventario
			</div>
		</div>
		<div class="w-10 h-10 rounded-full bg-emerald-50 flex items-center justify-center text-emerald-600 shrink-0">
			<CheckCircle2 class="w-5 h-5" />
		</div>
	</Card>

	<!-- Total Amount -->
	<Card class="p-4 border-l-4 border-l-blue-500 flex items-center justify-between">
		<div>
			<div class="text-2xs font-semibold text-gray-400 uppercase tracking-wider">
				Total Recibido (Costo Real)
			</div>
			<div class="text-xl sm:text-2xl font-bold text-gray-900 mt-1 truncate">
				{formatARS(kpis.totalAmountCommitted)}
			</div>
			<div class="text-2xs text-gray-500 font-medium mt-0.5">
				Con split fiscal e IVA incluido
			</div>
		</div>
		<div class="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center text-blue-600 shrink-0">
			<TrendingUp class="w-5 h-5" />
		</div>
	</Card>
</div>
