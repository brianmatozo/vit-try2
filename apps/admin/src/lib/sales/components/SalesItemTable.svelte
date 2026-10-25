<script lang="ts">
import { formatARS, formatWeight } from '@vitalcer/core';
import { Badge } from '@vitalcer/ui';
import { ExternalLink } from 'lucide-svelte';
import type { TicketGroup } from '../sales-metrics';

interface Props {
	ticket: TicketGroup;
}

let { ticket }: Props = $props();
</script>

<div class="border-t border-gray-100 bg-gray-50/50 p-4 space-y-3">
	<div class="text-xs font-bold uppercase tracking-wider text-gray-500">
		Desglose de Artículos
	</div>

	<div class="overflow-x-auto rounded-lg border border-gray-200 bg-white">
		<table class="w-full text-left text-xs text-gray-600">
			<thead class="bg-gray-50 text-gray-700 font-semibold border-b border-gray-200">
				<tr>
					<th scope="col" class="py-2.5 px-3">Artículo</th>
					<th scope="col" class="py-2.5 px-3">Tipo</th>
					<th scope="col" class="py-2.5 px-3 text-right">Cantidad</th>
					<th scope="col" class="py-2.5 px-3 text-right">Precio Unitario</th>
					<th scope="col" class="py-2.5 px-3 text-right">Subtotal</th>
					<th scope="col" class="py-2.5 px-3 text-center">Auditoría</th>
				</tr>
			</thead>
			<tbody class="divide-y divide-gray-100 font-medium">
				{#each ticket.items as item (item.ledgerId)}
					<tr class="hover:bg-gray-50/75 transition-colors">
						<td class="py-2.5 px-3">
							<div class="font-bold text-gray-900">{item.productName}</div>
							<div class="text-xs text-gray-400 font-mono">{item.sku}</div>
						</td>
						<td class="py-2.5 px-3">
							{#if item.productType === 'bulk'}
								<Badge variant="outline" class="text-2xs bg-purple-50 text-purple-700 border-purple-200">
									Granel
								</Badge>
							{:else}
								<Badge variant="outline" class="text-2xs bg-sky-50 text-sky-700 border-sky-200">
									Unidad
								</Badge>
							{/if}
						</td>
						<td class="py-2.5 px-3 text-right font-mono font-semibold text-gray-800">
							{#if item.productType === 'bulk'}
								{formatWeight(item.quantity)}
							{:else}
								{item.quantity} u.
							{/if}
						</td>
						<td class="py-2.5 px-3 text-right font-mono text-gray-700">
							{#if item.productType === 'bulk'}
								{formatARS(item.unitPrice)} / {item.bulkReferenceGrams ?? 100}g
							{:else}
								{formatARS(item.unitPrice)}
							{/if}
						</td>
						<td class="py-2.5 px-3 text-right font-mono font-bold text-emerald-700">
							{formatARS(item.subtotal)}
						</td>
						<td class="py-2.5 px-3 text-center">
							<a
								href={`/ledger?product_id=${item.productId}`}
								title="Ver auditoría de movimientos"
								class="inline-flex items-center gap-1 text-xs text-emerald-600 hover:text-emerald-700 hover:underline font-semibold"
							>
								<span>Ver</span>
								<ExternalLink class="w-3 h-3" />
							</a>
						</td>
					</tr>
				{/each}
			</tbody>
			<tfoot class="bg-gray-50/80 border-t border-gray-200 font-bold text-gray-900">
				<tr>
					<td colspan="4" class="py-2.5 px-3 text-right uppercase text-xs tracking-wider text-gray-500">
						Total Ticket:
					</td>
					<td class="py-2.5 px-3 text-right text-emerald-700 text-sm font-black font-mono">
						{formatARS(ticket.totalAmount)}
					</td>
					<td></td>
				</tr>
			</tfoot>
		</table>
	</div>
</div>
