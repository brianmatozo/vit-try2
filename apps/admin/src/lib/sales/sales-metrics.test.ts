import type { InventoryLedgerResponse, ProductResponse } from '@vitalcer/api';
import { describe, expect, it } from 'vitest';
import {
	calculateSalesKpis,
	filterTickets,
	formatTicketDate,
	groupLedgerSales,
	isToday,
	parseIsoDate,
} from './sales-metrics';

const mockDiscreteProduct: ProductResponse = {
	id: 1,
	sku: 'DISC-001',
	name: 'Galletitas Integrales',
	product_type: 'discrete',
	unit_price: 1500,
	current_stock: 40,
	reserved_stock: 0,
	virtual_stock: 40,
	is_active: true,
	created_at: '2026-01-01T00:00:00Z',
	updated_at: '2026-01-01T00:00:00Z',
};

const mockBulkProduct: ProductResponse = {
	id: 2,
	sku: 'BULK-002',
	plu_code: '2001',
	name: 'Nueces Pecán',
	product_type: 'bulk',
	unit_price: 6000,
	bulk_reference_grams: 100,
	current_stock: 10000,
	reserved_stock: 0,
	virtual_stock: 10000,
	is_active: true,
	created_at: '2026-01-01T00:00:00Z',
	updated_at: '2026-01-01T00:00:00Z',
};

const productsMap = new Map<number, ProductResponse>([
	[mockDiscreteProduct.id, mockDiscreteProduct],
	[mockBulkProduct.id, mockBulkProduct],
]);

describe('groupLedgerSales', () => {
	it('groups multiple sale_pos entries by reference_id and computes totals', () => {
		const entries: InventoryLedgerResponse[] = [
			{
				id: 101,
				product_id: 1,
				quantity_delta: -2,
				balance_after: 38,
				movement_type: 'sale_pos',
				reference_id: 'TKT-001',
				notes: null,
				created_at: '2026-10-25T10:00:00Z',
			},
			{
				id: 102,
				product_id: 2,
				quantity_delta: -250, // 250g
				balance_after: 9750,
				movement_type: 'sale_pos',
				reference_id: 'TKT-001',
				notes: null,
				created_at: '2026-10-25T10:00:00Z',
			},
		];

		const tickets = groupLedgerSales(entries, productsMap);
		expect(tickets).toHaveLength(1);

		const t = tickets[0];
		expect(t.ticketId).toBe('TKT-001');
		expect(t.items).toHaveLength(2);

		// Item 1: 2 discrete @ $1500 = $3000
		expect(t.items[0].productName).toBe('Galletitas Integrales');
		expect(t.items[0].quantity).toBe(2);
		expect(t.items[0].subtotal).toBe(3000);

		// Item 2: 250g of $6000/100g = 2.5 * 6000 = $15000
		expect(t.items[1].productName).toBe('Nueces Pecán');
		expect(t.items[1].quantity).toBe(250);
		expect(t.items[1].subtotal).toBe(15000);

		// Total: $3000 + $15000 = $18000
		expect(t.totalAmount).toBe(18000);
		expect(t.totalUnits).toBe(3); // 2 discrete units + 1 bulk packet
		expect(t.totalUnitsOrLines).toBe(3);
	});

	it('correctly parses naive ISO strings without timezone as UTC', () => {
		const entries: InventoryLedgerResponse[] = [
			{
				id: 110,
				product_id: 1,
				quantity_delta: -3,
				balance_after: 35,
				movement_type: 'sale_pos',
				reference_id: 'TKT-NAIVE',
				notes: null,
				created_at: '2026-10-29T02:07:08.402996',
			},
		];

		const tickets = groupLedgerSales(entries, productsMap);
		expect(tickets).toHaveLength(1);
		// In UTC-3, 2026-10-29 02:07:08 UTC is 2026-10-28 23:07:08 local
		const localDate = tickets[0].date;
		expect(localDate.getUTCHours()).toBe(2);
		expect(localDate.getUTCMinutes()).toBe(7);
		expect(tickets[0].totalUnits).toBe(3);
	});

	it('creates fallback ticket ID when reference_id is missing', () => {
		const entries: InventoryLedgerResponse[] = [
			{
				id: 103,
				product_id: 1,
				quantity_delta: -1,
				balance_after: 39,
				movement_type: 'sale_pos',
				reference_id: null,
				notes: null,
				created_at: '2026-10-25T10:30:00Z',
			},
		];

		const tickets = groupLedgerSales(entries, productsMap);
		expect(tickets).toHaveLength(1);
		expect(tickets[0].ticketId).toBe('POS-MOV-103');
	});

	it('ignores non-sale_pos movements', () => {
		const entries: InventoryLedgerResponse[] = [
			{
				id: 104,
				product_id: 1,
				quantity_delta: 50,
				balance_after: 90,
				movement_type: 'receiving',
				reference_id: 'REM-1',
				notes: null,
				created_at: '2026-10-25T08:00:00Z',
			},
			{
				id: 105,
				product_id: 1,
				quantity_delta: -5,
				balance_after: 85,
				movement_type: 'shrinkage_merma',
				reference_id: 'INC-1',
				notes: null,
				created_at: '2026-10-25T09:00:00Z',
			},
		];

		const tickets = groupLedgerSales(entries, productsMap);
		expect(tickets).toHaveLength(0);
	});

	it('gracefully handles missing product in productsMap', () => {
		const entries: InventoryLedgerResponse[] = [
			{
				id: 106,
				product_id: 999, // Unknown
				quantity_delta: -3,
				balance_after: 0,
				movement_type: 'sale_pos',
				reference_id: 'TKT-UNKNOWN',
				notes: null,
				created_at: '2026-10-25T11:00:00Z',
			},
		];

		const tickets = groupLedgerSales(entries, productsMap);
		expect(tickets).toHaveLength(1);
		expect(tickets[0].items[0].productName).toBe('Artículo #999');
		expect(tickets[0].items[0].sku).toBe('ID-999');
		expect(tickets[0].items[0].subtotal).toBe(0);
	});
});

describe('parseIsoDate', () => {
	it('handles timestamps ending with Z', () => {
		const d = parseIsoDate('2026-10-25T10:00:00Z');
		expect(d.getUTCHours()).toBe(10);
	});

	it('appends Z to naive timestamps lacking timezone info', () => {
		const d = parseIsoDate('2026-10-29T02:07:08.402996');
		expect(d.getUTCFullYear()).toBe(2026);
		expect(d.getUTCMonth()).toBe(9); // October
		expect(d.getUTCDate()).toBe(29);
		expect(d.getUTCHours()).toBe(2);
		expect(d.getUTCMinutes()).toBe(7);
	});

	it('preserves timestamps with explicit timezone offsets', () => {
		const d = parseIsoDate('2026-10-28T23:07:08-03:00');
		expect(d.getUTCHours()).toBe(2);
		expect(d.getUTCDate()).toBe(29);
	});
});

describe('isToday', () => {
	it('correctly identifies today vs different dates', () => {
		const fixedNow = new Date('2026-10-25T14:00:00Z');
		const todayDate = new Date('2026-10-25T08:30:00Z');
		const yesterdayDate = new Date('2026-10-24T22:00:00Z');

		expect(isToday(todayDate, fixedNow)).toBe(true);
		expect(isToday(yesterdayDate, fixedNow)).toBe(false);
	});
});

describe('calculateSalesKpis', () => {
	it('calculates KPIs correctly for today and historical tickets', () => {
		const fixedNow = new Date('2026-10-25T12:00:00Z');
		const tickets = [
			{
				ticketId: 'TKT-TODAY-1',
				createdAt: '2026-10-25T10:00:00Z',
				date: new Date('2026-10-25T10:00:00Z'),
				items: [],
				totalAmount: 10000,
				totalUnits: 2,
				totalUnitsOrLines: 2,
			},
			{
				ticketId: 'TKT-TODAY-2',
				createdAt: '2026-10-25T11:00:00Z',
				date: new Date('2026-10-25T11:00:00Z'),
				items: [],
				totalAmount: 20000,
				totalUnits: 3,
				totalUnitsOrLines: 3,
			},
			{
				ticketId: 'TKT-PAST-1',
				createdAt: '2026-10-20T11:00:00Z',
				date: new Date('2026-10-20T11:00:00Z'),
				items: [],
				totalAmount: 50000,
				totalUnits: 5,
				totalUnitsOrLines: 5,
			},
		];

		const kpis = calculateSalesKpis(tickets, fixedNow);
		expect(kpis.totalRevenueToday).toBe(30000);
		expect(kpis.todayTicketsCount).toBe(2);
		expect(kpis.totalTicketsCount).toBe(3);
		expect(kpis.averageTicketToday).toBe(15000);
		expect(kpis.totalItemsSoldToday).toBe(5);
	});

	it('returns 0 average ticket when no tickets today', () => {
		const fixedNow = new Date('2026-10-25T12:00:00Z');
		const tickets = [
			{
				ticketId: 'TKT-PAST-1',
				createdAt: '2026-10-20T11:00:00Z',
				date: new Date('2026-10-20T11:00:00Z'),
				items: [],
				totalAmount: 50000,
				totalUnits: 5,
				totalUnitsOrLines: 5,
			},
		];

		const kpis = calculateSalesKpis(tickets, fixedNow);
		expect(kpis.todayTicketsCount).toBe(0);
		expect(kpis.averageTicketToday).toBe(0);
	});
});

describe('filterTickets', () => {
	const tickets = [
		{
			ticketId: 'TKT-100',
			createdAt: '2026-10-25T10:00:00Z',
			date: new Date('2026-10-25T10:00:00Z'),
			items: [
				{
					ledgerId: 1,
					productId: 1,
					productName: 'Galletitas Integrales',
					sku: 'DISC-001',
					productType: 'discrete' as const,
					quantity: 1,
					unitPrice: 1500,
					subtotal: 1500,
				},
			],
			totalAmount: 1500,
			totalUnits: 1,
			totalUnitsOrLines: 1,
		},
		{
			ticketId: 'TKT-200',
			createdAt: '2026-10-25T11:00:00Z',
			date: new Date('2026-10-25T11:00:00Z'),
			items: [
				{
					ledgerId: 2,
					productId: 2,
					productName: 'Nueces Pecán',
					sku: 'BULK-002',
					productType: 'bulk' as const,
					quantity: 200,
					unitPrice: 6000,
					subtotal: 12000,
				},
			],
			totalAmount: 12000,
			totalUnits: 1,
			totalUnitsOrLines: 1,
		},
	];

	it('returns all tickets when searchTerm is empty', () => {
		expect(filterTickets(tickets, '')).toEqual(tickets);
		expect(filterTickets(tickets, '   ')).toEqual(tickets);
	});

	it('filters by ticket ID', () => {
		const res = filterTickets(tickets, '100');
		expect(res).toHaveLength(1);
		expect(res[0].ticketId).toBe('TKT-100');
	});

	it('filters by product name', () => {
		const res = filterTickets(tickets, 'pecán');
		expect(res).toHaveLength(1);
		expect(res[0].ticketId).toBe('TKT-200');
	});

	it('filters by SKU', () => {
		const res = filterTickets(tickets, 'disc-001');
		expect(res).toHaveLength(1);
		expect(res[0].ticketId).toBe('TKT-100');
	});
});

describe('formatTicketDate', () => {
	it('formats valid ISO dates', () => {
		const formatted = formatTicketDate('2026-10-25T10:30:00Z');
		expect(formatted).toBeTruthy();
		expect(typeof formatted).toBe('string');
	});

	it('safely returns fallback on invalid dates', () => {
		expect(formatTicketDate('invalid-date')).toBe('invalid-date');
	});
});
