<script lang="ts">
import { Badge, Button } from '@vitalcer/ui';
import {
	AlertCircle,
	AlertTriangle,
	ArrowLeft,
	CheckCircle,
	XCircle,
} from 'lucide-svelte';
import type { RemitoDetailState } from '../remito-detail-state.svelte';

interface Props {
	remitoId: number;
	detailState: RemitoDetailState;
	actionFeedback: string | null;
	onConfirm: () => Promise<void>;
	onReject: () => Promise<void>;
}

let { remitoId, detailState, actionFeedback, onConfirm, onReject }: Props =
	$props();
</script>

<div class="space-y-3">
	<!-- Top Bar -->
	<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-gray-200">
		<div class="flex items-center gap-3">
			<a href="/remitos">
				<Button variant="outline" size="sm" class="h-8 w-8 p-0">
					<ArrowLeft class="w-4 h-4" />
				</Button>
			</a>
			<div>
				<div class="flex items-center gap-2">
					<h1 class="text-lg font-bold text-gray-900">
						{detailState.remito?.supplier_name || 'Cargando remito...'}
					</h1>
					{#if detailState.remito?.status === 'staged'}
						<Badge variant="warning" class="font-bold">🟡 STAGED</Badge>
					{:else if detailState.remito?.status === 'committed'}
						<Badge variant="success" class="font-bold">🟢 CONFIRMADO</Badge>
					{:else if detailState.remito}
						<Badge variant="outline">{detailState.remito.status}</Badge>
					{/if}
				</div>
				<div class="text-2xs text-gray-400 mt-0.5 flex items-center gap-2">
					<span>Comprobante: {detailState.remito?.remito_number || `#${remitoId}`}</span>
					<span>•</span>
					<span>{detailState.remito?.items ? detailState.remito.items.length : 0} ítems detectados</span>
				</div>
			</div>
		</div>

		<!-- Action Confirmation Bar -->
		{#if detailState.remito?.status === 'staged'}
			<div class="flex items-center gap-2">
				<Button
					variant="outline"
					size="sm"
					disabled={detailState.isRejecting}
					onclick={onReject}
					class="border-rose-300 text-rose-700 hover:bg-rose-50 text-xs"
				>
					<XCircle class="w-4 h-4 mr-1 text-rose-500" />
					<span>Descartar</span>
				</Button>

				<Button
					size="sm"
					disabled={!detailState.canConfirm}
					onclick={onConfirm}
					class="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold gap-1.5 shadow-sm text-xs disabled:opacity-50"
				>
					<CheckCircle class="w-4 h-4" />
					<span>{detailState.isConfirming ? 'Imputando...' : 'Confirmar Stock'}</span>
				</Button>
			</div>
		{/if}
	</div>

	{#if actionFeedback}
		<div class="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center gap-2">
			<CheckCircle class="w-4 h-4 text-emerald-600 shrink-0" />
			<span>{actionFeedback}</span>
		</div>
	{/if}

	<!-- Low OCR Confidence Banner -->
	{#if detailState.isLowConfidence && detailState.remito?.status === 'staged'}
		<div class="p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center gap-2">
			<AlertCircle class="w-4 h-4 text-amber-600 shrink-0" />
			<span>
				⚠️ Comprobante con baja legibilidad (confianza general {detailState.remito?.overall_confidence}%). Verifique detenidamente los ítems contra la foto.
			</span>
		</div>
	{/if}

	<!-- Discrepancy Warning Banner -->
	{#if detailState.hasSignificantDiscrepancy && detailState.remito?.status === 'staged'}
		<div class="p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center justify-between">
			<div class="flex items-center gap-2">
				<AlertTriangle class="w-4 h-4 text-amber-600 shrink-0" />
				<span>
					⚠️ La suma de líneas (${detailState.computedLinesSum.toLocaleString('es-AR')}) difiere del total del comprobante (${(detailState.remito?.total_raw_amount || 0).toLocaleString('es-AR')}) en ${detailState.discrepancyArs.toLocaleString('es-AR')}. Revise las cantidades y precios.
				</span>
			</div>
		</div>
	{/if}

	<!-- Unmatched Items Warning Gate -->
	{#if detailState.unmatchedCount > 0 && detailState.remito?.status === 'staged'}
		<div class="p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-900 text-xs flex items-center justify-between">
			<div class="flex items-center gap-2">
				<AlertCircle class="w-4 h-4 text-rose-600 shrink-0" />
				<span>Hay {detailState.unmatchedCount} artículo(s) sin vincular a catálogo (🔴). Debés asociarlos o ponerlos en 0 para confirmar.</span>
			</div>
		</div>
	{/if}
</div>
