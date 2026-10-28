<script lang="ts">
import type { ProductResponse, RemitoItemResponse } from '@vitalcer/api';
import { formatARS } from '@vitalcer/core';
import { Card } from '@vitalcer/ui';
import { AlertTriangle } from 'lucide-svelte';
import type { RemitoDetailState } from '../remito-detail-state.svelte';
import RemitoItemRow from './RemitoItemRow.svelte';

interface Props {
	detailState: RemitoDetailState;
	products: ProductResponse[];
	onUpdateItem: (
		itemId: number,
		updates: {
			effective_quantity?: number;
			multiplier?: number;
			product_id?: number;
			is_verified_by_user?: boolean;
		},
	) => Promise<void>;
}

let { detailState, products, onUpdateItem }: Props = $props();

const items = $derived(detailState.remito?.items || []);
</script>

<div class="space-y-3">
	<!-- Mathematical Audit Discrepancy Warning Banner -->
	{#if detailState.hasSignificantDiscrepancy}
		<div class="p-3 rounded-lg bg-amber-50 border border-amber-200 flex items-start gap-2.5 text-amber-900 text-xs">
			<AlertTriangle class="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
			<div>
				<span class="font-bold">Advertencia de auditoría:</span>
				La suma de las líneas extraídas ({formatARS(detailState.computedLinesSum)}) difiere del total impreso en el comprobante ({formatARS(detailState.remito?.total_raw_amount || 0)}) en {formatARS(detailState.discrepancyArs)}.
				Verificá las cantidades y precios unitarios extraídos antes de confirmar.
			</div>
		</div>
	{/if}

	<!-- Items Audit Table -->
	<Card class="overflow-hidden border border-gray-200">
		<div class="overflow-x-auto">
			<table class="w-full text-left text-xs">
				<thead class="bg-gray-50 border-b border-gray-200 text-gray-500 font-semibold uppercase text-2xs tracking-wider">
					<tr>
						<th class="py-2.5 px-3">Estado</th>
						<th class="py-2.5 px-3">Descripción Impresa</th>
						<th class="py-2.5 px-3">Producto Asociado (Catálogo)</th>
						<th class="py-2.5 px-3 text-center">Pack ×</th>
						<th class="py-2.5 px-3 text-center">Recibido</th>
						<th class="py-2.5 px-3 text-right">A Imputar</th>
						<th class="py-2.5 px-3 text-right">Costo Neto</th>
						<th class="py-2.5 px-3 text-right"></th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100">
					{#each items as it (it.id)}
						<RemitoItemRow
							item={it}
							{products}
							onUpdate={onUpdateItem}
							onCreateProduct={(item) => detailState.openQuickProduct(item)}
						/>
					{:else}
						<tr>
							<td colspan="8" class="p-6 text-center text-gray-400">
								No hay ítems registrados en este remito
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</Card>
</div>
