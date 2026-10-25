import type { ProductResponse } from '@vitalcer/api';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { CartItem } from '$lib/cart/cart.svelte';
import { type BatchSaleApiFn, CheckoutState } from './checkout-state.svelte';

vi.mock('$lib/audio/sound', () => ({
	playError: vi.fn().mockResolvedValue(undefined),
	playSuccess: vi.fn().mockResolvedValue(undefined),
}));

const mockProductDiscrete: ProductResponse = {
	id: 1,
	sku: 'DISC-1',
	name: 'Barrita de Cereal',
	product_type: 'discrete',
	unit_price: 1000,
	current_stock: 50,
	reserved_stock: 0,
	virtual_stock: 50,
	is_active: true,
	created_at: '2026-01-01T00:00:00Z',
	updated_at: '2026-01-01T00:00:00Z',
};

const mockProductBulk: ProductResponse = {
	id: 2,
	sku: 'BULK-2',
	name: 'Mix Frutos Secos',
	product_type: 'bulk',
	unit_price: 3000,
	bulk_reference_grams: 100,
	current_stock: 10000,
	reserved_stock: 0,
	virtual_stock: 10000,
	is_active: true,
	created_at: '2026-01-01T00:00:00Z',
	updated_at: '2026-01-01T00:00:00Z',
};

const mockCartItems: CartItem[] = [
	{
		id: 'item-1',
		product: mockProductDiscrete,
		isBulk: false,
		quantity: 2,
		unitPrice: 1000,
		lineTotal: 2000,
	},
	{
		id: 'item-2',
		product: mockProductBulk,
		isBulk: true,
		quantity: 1,
		weightGrams: 200,
		unitPrice: 3000,
		lineTotal: 6000,
	},
];

describe('CheckoutState', () => {
	let checkout: CheckoutState;

	beforeEach(() => {
		checkout = new CheckoutState();
	});

	afterEach(() => {
		vi.clearAllMocks();
	});

	it('initializes with default values', () => {
		expect(checkout.paymentMethod).toBe('cash');
		expect(checkout.cashTendered).toBe(0);
		expect(checkout.isProcessing).toBe(false);
		expect(checkout.errorMessage).toBeNull();
		expect(checkout.completedTicket).toBeNull();
	});

	it('calculates cash change and validates cash tendered', () => {
		checkout.initCash(8000);
		expect(checkout.cashTendered).toBe(8000);
		expect(checkout.getChange(8000)).toBe(0);
		expect(checkout.isCashValid(8000)).toBe(true);

		checkout.setCashAmount(10000);
		expect(checkout.getChange(8000)).toBe(2000);
		expect(checkout.isCashValid(8000)).toBe(true);

		checkout.setCashAmount(5000);
		expect(checkout.getChange(8000)).toBe(-3000);
		expect(checkout.isCashValid(8000)).toBe(false);

		// Non-cash methods are always valid regardless of cashTendered
		checkout.paymentMethod = 'card';
		expect(checkout.isCashValid(8000)).toBe(true);
	});

	it('handles quick-bill presets correctly', () => {
		const total = 4500;
		checkout.setCashAmount(2000); // Less than total

		// When cashTendered < total, adding replaces the amount
		checkout.addCashAmount(5000, total);
		expect(checkout.cashTendered).toBe(5000);

		// When cashTendered >= total, adding increases the amount
		checkout.addCashAmount(2000, total);
		expect(checkout.cashTendered).toBe(7000);
	});

	it('rejects confirmation when cash tendered is less than total', async () => {
		checkout.setCashAmount(5000);
		const onComplete = vi.fn();
		const mockApi = vi.fn() as unknown as BatchSaleApiFn;

		const success = await checkout.confirmSale(
			mockCartItems,
			8000,
			3,
			onComplete,
			mockApi,
		);

		expect(success).toBe(false);
		expect(checkout.errorMessage).toContain('menor al total');
		expect(mockApi).not.toHaveBeenCalled();
		expect(onComplete).not.toHaveBeenCalled();
	});

	it('successfully processes sale and maps bulk weight vs discrete quantity in payload', async () => {
		checkout.setCashAmount(10000);
		const onComplete = vi.fn();
		const mockApi = vi.fn().mockResolvedValue({
			data: { message: 'Sale recorded' },
		}) as unknown as BatchSaleApiFn;

		const success = await checkout.confirmSale(
			mockCartItems,
			8000,
			3,
			onComplete,
			mockApi,
		);

		expect(success).toBe(true);
		expect(checkout.errorMessage).toBeNull();
		expect(onComplete).toHaveBeenCalled();
		expect(checkout.completedTicket).toBeTruthy();
		expect(checkout.completedTicket?.total).toBe(8000);
		expect(checkout.completedTicket?.change).toBe(2000);
		expect(checkout.completedTicket?.itemCount).toBe(3);

		// Verify API was called with discrete items using quantity and bulk using weightGrams
		expect(mockApi).toHaveBeenCalledWith({
			body: {
				ticket_reference_id: expect.stringMatching(/^POS-\d+/),
				items: [
					{ product_id: 1, quantity: 2 },
					{ product_id: 2, quantity: 200 },
				],
			},
		});
	});

	it('handles API error response gracefully', async () => {
		checkout.setCashAmount(8000);
		const onComplete = vi.fn();
		const mockApi = vi.fn().mockResolvedValue({
			error: { detail: 'Stock insuficiente para el producto #2' },
		}) as unknown as BatchSaleApiFn;

		const success = await checkout.confirmSale(
			mockCartItems,
			8000,
			3,
			onComplete,
			mockApi,
		);

		expect(success).toBe(false);
		expect(checkout.errorMessage).toBe(
			'Stock insuficiente para el producto #2',
		);
		expect(onComplete).not.toHaveBeenCalled();
		expect(checkout.completedTicket).toBeNull();
	});

	it('resets state correctly with reset()', () => {
		checkout.paymentMethod = 'card';
		checkout.cashTendered = 15000;
		checkout.errorMessage = 'Some error';

		checkout.reset(5000);
		expect(checkout.paymentMethod).toBe('cash');
		expect(checkout.cashTendered).toBe(5000);
		expect(checkout.errorMessage).toBeNull();
		expect(checkout.isProcessing).toBe(false);
		expect(checkout.completedTicket).toBeNull();
	});
});
