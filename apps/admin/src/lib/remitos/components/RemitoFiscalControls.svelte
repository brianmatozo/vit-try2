<script lang="ts">
import { formatARS } from '@vitalcer/core';
import { Card, Input } from '@vitalcer/ui';
import { Calculator } from 'lucide-svelte';
import type { RemitoDetailState } from '../remito-detail-state.svelte';

interface Props {
	detailState: RemitoDetailState;
	onChangeSplit: (blanco: number, negro: number, iva: number) => Promise<void>;
}

let { detailState, onChangeSplit }: Props = $props();

let isUpdating = $state(false);

async function handleSliderChange(e: Event): Promise<void> {
	const val = Number((e.target as HTMLInputElement).value);
	const blanco = Math.max(0, Math.min(100, val));
	const negro = 100 - blanco;
	detailState.updateFiscalSplit(blanco, negro);

	isUpdating = true;
	try {
		await onChangeSplit(blanco, negro, detailState.ivaPct);
	} finally {
		isUpdating = false;
	}
}

async function handleIvaChange(e: Event): Promise<void> {
	const val = Number((e.target as HTMLInputElement).value);
	const iva = Math.max(0, Math.min(50, val));
	detailState.updateFiscalSplit(
		detailState.fiscalBlancoPct,
		detailState.fiscalNegroPct,
		iva,
	);

	isUpdating = true;
	try {
		await onChangeSplit(
			detailState.fiscalBlancoPct,
			detailState.fiscalNegroPct,
			iva,
		);
	} finally {
		isUpdating = false;
	}
}
</script>

<Card class="p-4 bg-gray-50/80 border border-gray-200 text-xs space-y-3">
	<div class="flex items-center justify-between">
		<div class="font-bold text-gray-800 flex items-center gap-1.5">
			<Calculator class="w-4 h-4 text-emerald-600" />
			<span>Split Fiscal Argentino & Costo Real</span>
		</div>
		{#if isUpdating}
			<span class="text-2xs font-semibold text-emerald-600 animate-pulse">
				Recalculando costos...
			</span>
		{/if}
	</div>

	<!-- Sliders & Split Summary -->
	<div class="space-y-2">
		<div class="flex items-center justify-between text-2xs font-semibold">
			<span class="text-blue-700">Blanco: {detailState.fiscalBlancoPct}% (+ {detailState.ivaPct}% IVA)</span>
			<span class="text-gray-700">Negro: {detailState.fiscalNegroPct}%</span>
		</div>

		<input
			type="range"
			min="0"
			max="100"
			value={detailState.fiscalBlancoPct}
			oninput={handleSliderChange}
			class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-emerald-600"
		/>
	</div>

	<!-- Totals Summary Bar -->
	<div class="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-2 border-t border-gray-200 text-2xs">
		<div>
			<span class="text-gray-500 block">Total Factura / Remito:</span>
			<span class="text-xs font-mono font-bold text-gray-700">
				{formatARS(detailState.remito?.total_raw_amount || 0)}
			</span>
		</div>

		<div>
			<span class="text-gray-500 block">Total Real con IVA:</span>
			<span class="text-xs font-mono font-bold text-emerald-700">
				{formatARS(detailState.remito?.total_real_amount || 0)}
			</span>
		</div>

		<div class="col-span-2 sm:col-span-1 flex items-center gap-2">
			<label for="iva-rate-input" class="text-gray-500 whitespace-nowrap">Alícuota IVA:</label>
			<Input
				id="iva-rate-input"
				type="number"
				value={detailState.ivaPct}
				onchange={handleIvaChange}
				class="w-16 h-7 text-xs font-bold font-mono text-center py-0"
			/>
			<span class="text-gray-500">%</span>
		</div>
	</div>
</Card>
