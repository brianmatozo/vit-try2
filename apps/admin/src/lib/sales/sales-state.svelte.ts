import type { InventoryLedgerResponse, ProductResponse } from '@vitalcer/api';
import { SvelteMap, SvelteSet } from 'svelte/reactivity';
import {
	calculateSalesKpis,
	filterTickets,
	groupLedgerSales,
	type SalesKpiMetrics,
	type TicketGroup,
} from './sales-metrics';

export class SalesState {
	searchTerm = $state('');
	ledgerEntries = $state<InventoryLedgerResponse[]>([]);
	productsList = $state<ProductResponse[]>([]);

	expandedTicketIds = new SvelteSet<string>();

	productsMap = $derived.by<Map<number, ProductResponse>>(() => {
		const map = new SvelteMap<number, ProductResponse>();
		for (const p of this.productsList) {
			map.set(p.id, p);
		}
		return map;
	});

	tickets = $derived.by<TicketGroup[]>(() => {
		return groupLedgerSales(this.ledgerEntries, this.productsMap);
	});

	filteredTickets = $derived.by<TicketGroup[]>(() => {
		return filterTickets(this.tickets, this.searchTerm);
	});

	kpis = $derived.by<SalesKpiMetrics>(() => {
		return calculateSalesKpis(this.tickets);
	});

	toggleExpand(ticketId: string): void {
		if (this.expandedTicketIds.has(ticketId)) {
			this.expandedTicketIds.delete(ticketId);
		} else {
			this.expandedTicketIds.add(ticketId);
		}
	}

	isExpanded(ticketId: string): boolean {
		return this.expandedTicketIds.has(ticketId);
	}

	expandAll(): void {
		for (const t of this.filteredTickets) {
			this.expandedTicketIds.add(t.ticketId);
		}
	}

	collapseAll(): void {
		this.expandedTicketIds.clear();
	}

	clearSearch(): void {
		this.searchTerm = '';
	}
}
