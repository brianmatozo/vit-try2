import type { InventoryLedgerResponse, ProductResponse } from '@vitalcer/api';
import { beforeEach, describe, expect, it } from 'vitest';
import { SalesState } from './sales-state.svelte';

const mockProduct: ProductResponse = {
	id: 1,
	sku: 'ALF-001',
	name: 'Alfajor de Algarroba',
	product_type: 'discrete',
	unit_price: 1800,
	current_stock: 50,
	reserved_stock: 0,
	virtual_stock: 50,
	is_active: true,
	created_at: '2026-01-01T00:00:00Z',
	updated_at: '2026-01-01T00:00:00Z',
};

const mockLedgerEntry: InventoryLedgerResponse = {
	id: 501,
	product_id: 1,
	quantity_delta: -2,
	balance_after: 48,
	movement_type: 'sale_pos',
	reference_id: 'POS-TKT-501',
	notes: null,
	created_at: new Date().toISOString(),
};

describe('SalesState', () => {
	let state: SalesState;

	beforeEach(() => {
		state = new SalesState();
	});

	it('initializes with default empty state', () => {
		expect(state.searchTerm).toBe('');
		expect(state.ledgerEntries).toEqual([]);
		expect(state.productsList).toEqual([]);
		expect(state.tickets).toEqual([]);
		expect(state.filteredTickets).toEqual([]);
		expect(state.kpis.totalRevenueToday).toBe(0);
	});

	it('derives tickets and KPIs reactively when data is populated', () => {
		state.productsList = [mockProduct];
		state.ledgerEntries = [mockLedgerEntry];

		expect(state.productsMap.get(1)).toEqual(mockProduct);
		expect(state.tickets).toHaveLength(1);
		expect(state.tickets[0].ticketId).toBe('POS-TKT-501');
		expect(state.tickets[0].totalAmount).toBe(3600); // 2 * 1800

		expect(state.kpis.todayTicketsCount).toBe(1);
		expect(state.kpis.totalRevenueToday).toBe(3600);
	});

	it('toggles ticket expansion correctly', () => {
		expect(state.isExpanded('TKT-1')).toBe(false);

		state.toggleExpand('TKT-1');
		expect(state.isExpanded('TKT-1')).toBe(true);

		state.toggleExpand('TKT-1');
		expect(state.isExpanded('TKT-1')).toBe(false);
	});

	it('expands all filtered tickets and collapses all', () => {
		state.productsList = [mockProduct];
		state.ledgerEntries = [
			mockLedgerEntry,
			{
				...mockLedgerEntry,
				id: 502,
				reference_id: 'POS-TKT-502',
			},
		];

		expect(state.filteredTickets).toHaveLength(2);

		state.expandAll();
		expect(state.isExpanded('POS-TKT-501')).toBe(true);
		expect(state.isExpanded('POS-TKT-502')).toBe(true);

		state.collapseAll();
		expect(state.isExpanded('POS-TKT-501')).toBe(false);
		expect(state.isExpanded('POS-TKT-502')).toBe(false);
	});

	it('filters tickets by search term and clears search', () => {
		state.productsList = [mockProduct];
		state.ledgerEntries = [
			mockLedgerEntry,
			{
				...mockLedgerEntry,
				id: 502,
				reference_id: 'OTHER-TKT',
			},
		];

		state.searchTerm = 'POS-TKT';
		expect(state.filteredTickets).toHaveLength(1);
		expect(state.filteredTickets[0].ticketId).toBe('POS-TKT-501');

		state.clearSearch();
		expect(state.searchTerm).toBe('');
		expect(state.filteredTickets).toHaveLength(2);
	});
});
