import type { InventoryLedgerResponse, ProductResponse } from '@vitalcer/api';
import { calculateBulkLineTotal } from '@vitalcer/core';

export interface TicketItem {
	ledgerId: number;
	productId: number;
	productName: string;
	sku: string;
	productType: 'bulk' | 'discrete';
	quantity: number;
	unitPrice: number;
	bulkReferenceGrams?: number;
	subtotal: number;
}

export interface TicketGroup {
	ticketId: string;
	createdAt: string;
	date: Date;
	items: TicketItem[];
	totalAmount: number;
	totalUnits: number;
	totalUnitsOrLines: number;
}

export interface SalesKpiMetrics {
	totalRevenueToday: number;
	todayTicketsCount: number;
	totalTicketsCount: number;
	averageTicketToday: number;
	totalItemsSoldToday: number;
}

/**
 * Safely parses an ISO date string, ensuring strings without explicit timezone
 * indicators are treated as UTC so local day comparisons are accurate.
 */
export function parseIsoDate(isoDate: string): Date {
	if (!isoDate) return new Date();
	const hasTimezone =
		isoDate.endsWith('Z') || /[+-]\d{2}:?\d{2}$/.test(isoDate);
	const normalized = hasTimezone ? isoDate : `${isoDate}Z`;
	return new Date(normalized);
}

/**
 * Groups raw immutable ledger sales entries by ticket reference ID.
 */
export function groupLedgerSales(
	entries: InventoryLedgerResponse[],
	productsMap: Map<number, ProductResponse>,
): TicketGroup[] {
	const map = new Map<string, TicketGroup>();

	for (const entry of entries) {
		if (entry.movement_type !== 'sale_pos') continue;

		const ticketId = entry.reference_id || `POS-MOV-${entry.id}`;
		let group = map.get(ticketId);
		if (!group) {
			group = {
				ticketId,
				createdAt: entry.created_at,
				date: parseIsoDate(entry.created_at),
				items: [],
				totalAmount: 0,
				totalUnits: 0,
				totalUnitsOrLines: 0,
			};
			map.set(ticketId, group);
		}

		const product = productsMap.get(entry.product_id);
		const qty = Math.abs(entry.quantity_delta);

		let subtotal = 0;
		let productName = `Artículo #${entry.product_id}`;
		let sku = `ID-${entry.product_id}`;
		let productType: 'bulk' | 'discrete' = 'discrete';
		let unitPrice = 0;
		let bulkReferenceGrams: number | undefined;

		if (product) {
			productName = product.name;
			sku = product.sku;
			productType = product.product_type ?? 'discrete';
			unitPrice = product.unit_price;
			bulkReferenceGrams = product.bulk_reference_grams ?? 100;

			if (productType === 'bulk') {
				subtotal = calculateBulkLineTotal(unitPrice, bulkReferenceGrams, qty);
			} else {
				subtotal = qty * unitPrice;
			}
		}

		group.items.push({
			ledgerId: entry.id,
			productId: entry.product_id,
			productName,
			sku,
			productType,
			quantity: qty,
			unitPrice,
			bulkReferenceGrams,
			subtotal,
		});

		const units = productType === 'bulk' ? 1 : qty;
		group.totalAmount += subtotal;
		group.totalUnits += units;
		group.totalUnitsOrLines = group.totalUnits;
	}

	return Array.from(map.values()).sort(
		(a, b) => b.date.getTime() - a.date.getTime(),
	);
}

/**
 * Checks if a given Date matches today's calendar date.
 */
export function isToday(d: Date, now: Date = new Date()): boolean {
	return (
		d.getDate() === now.getDate() &&
		d.getMonth() === now.getMonth() &&
		d.getFullYear() === now.getFullYear()
	);
}

/**
 * Calculates high-level POS sales KPIs scoped to today.
 */
export function calculateSalesKpis(
	tickets: TicketGroup[],
	now: Date = new Date(),
): SalesKpiMetrics {
	const todayTickets = tickets.filter((t) => isToday(t.date, now));
	const totalRevenueToday = todayTickets.reduce(
		(acc, t) => acc + t.totalAmount,
		0,
	);
	const todayTicketsCount = todayTickets.length;
	const totalTicketsCount = tickets.length;
	const averageTicketToday =
		todayTicketsCount > 0
			? Math.round(totalRevenueToday / todayTicketsCount)
			: 0;
	const totalItemsSoldToday = todayTickets.reduce(
		(acc, t) => acc + (t.totalUnits ?? t.totalUnitsOrLines ?? 0),
		0,
	);

	return {
		totalRevenueToday,
		todayTicketsCount,
		totalTicketsCount,
		averageTicketToday,
		totalItemsSoldToday,
	};
}

/**
 * Filters tickets by ticket ID, product name, or SKU.
 */
export function filterTickets(
	tickets: TicketGroup[],
	searchTerm: string,
): TicketGroup[] {
	const term = searchTerm.trim().toLowerCase();
	if (!term) return tickets;

	return tickets.filter((t) => {
		if (t.ticketId.toLowerCase().includes(term)) return true;
		return t.items.some(
			(item) =>
				item.productName.toLowerCase().includes(term) ||
				item.sku.toLowerCase().includes(term),
		);
	});
}

/**
 * Formats ISO timestamp to Argentine standard datetime format.
 */
export function formatTicketDate(isoDate: string): string {
	const d = parseIsoDate(isoDate);
	if (Number.isNaN(d.getTime())) return isoDate;
	return d.toLocaleString('es-AR', {
		day: '2-digit',
		month: '2-digit',
		year: 'numeric',
		hour: '2-digit',
		minute: '2-digit',
	});
}
