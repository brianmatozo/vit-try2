<script lang="ts">
import { formatARS } from '@vitalcer/core';
import { Badge, Card } from '@vitalcer/ui';
import { Calendar, ChevronDown, ChevronUp, Receipt } from 'lucide-svelte';
import { formatTicketDate, type TicketGroup } from '../sales-metrics';
import SalesItemTable from './SalesItemTable.svelte';

interface Props {
	ticket: TicketGroup;
	isExpanded: boolean;
	onToggle: () => void;
}

let { ticket, isExpanded, onToggle }: Props = $props();
</script>

<Card class="overflow-hidden border-gray-200 transition-all hover:border-gray-300">
	<!-- Ticket Summary Row -->
	<div
		role="button"
		tabindex="0"
		onclick={onToggle}
		onkeydown={(e) => {
			if (e.key === 'Enter' || e.key === ' ') {
				e.preventDefault();
				onToggle();
			}
		}}
		class="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 cursor-pointer bg-white hover:bg-gray-50/75 transition-colors select-none"
	>
		<div class="flex items-start sm:items-center gap-3">
			<div class="p-2.5 rounded-xl bg-neutral-100 text-neutral-700 shrink-0 mt-0.5 sm:mt-0">
				<Receipt class="w-5 h-5" />
			</div>

			<div>
				<div class="flex items-center gap-2 flex-wrap">
					<span class="font-mono font-bold text-sm text-gray-900 tracking-tight">
						#{ticket.ticketId}
					</span>
					<Badge variant="outline" class="text-xs font-medium py-0 px-2 bg-gray-50 text-gray-600">
						{ticket.items.length} {ticket.items.length === 1 ? 'artículo' : 'artículos'}
					</Badge>
				</div>
				<div class="flex items-center gap-1.5 text-xs text-gray-500 mt-1">
					<Calendar class="w-3.5 h-3.5 text-gray-400" />
					<span>{formatTicketDate(ticket.createdAt)}</span>
				</div>
			</div>
		</div>

		<div class="flex items-center justify-between sm:justify-end gap-4 pt-2 sm:pt-0 border-t sm:border-t-0 border-gray-100">
			<div class="text-right">
				<div class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Total</div>
				<div class="text-lg font-black text-emerald-600">
					{formatARS(ticket.totalAmount)}
				</div>
			</div>

			<button
				type="button"
				class="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
				aria-label={isExpanded ? 'Contraer ticket' : 'Ver detalle del ticket'}
			>
				{#if isExpanded}
					<ChevronUp class="w-5 h-5" />
				{:else}
					<ChevronDown class="w-5 h-5" />
				{/if}
			</button>
		</div>
	</div>

	<!-- Expandable Item Breakdown -->
	{#if isExpanded}
		<SalesItemTable {ticket} />
	{/if}
</Card>
