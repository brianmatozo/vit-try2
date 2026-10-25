import type { ProductResponse } from '@vitalcer/api';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cart } from '$lib/cart/cart.svelte';
import { CounterState } from './counter-state.svelte';

vi.mock('$lib/audio/sound', () => ({
	playBeep: vi.fn().mockResolvedValue(undefined),
	playError: vi.fn().mockResolvedValue(undefined),
}));

const mockProduct: ProductResponse = {
	id: 10,
	sku: 'ALM-100',
	name: 'Almendras Nonpareil',
	product_type: 'bulk',
	unit_price: 3000,
	bulk_reference_grams: 100,
	current_stock: 5000,
	reserved_stock: 0,
	virtual_stock: 5000,
	is_active: true,
	created_at: '2026-01-01T00:00:00Z',
	updated_at: '2026-01-01T00:00:00Z',
};

const mockDiscrete: ProductResponse = {
	id: 20,
	sku: 'DISC-20',
	name: 'Alfajor Vegano',
	product_type: 'discrete',
	unit_price: 1200,
	current_stock: 30,
	reserved_stock: 0,
	virtual_stock: 30,
	is_active: true,
	created_at: '2026-01-01T00:00:00Z',
	updated_at: '2026-01-01T00:00:00Z',
};

describe('CounterState', () => {
	let counter: CounterState;

	beforeEach(() => {
		cart.clearCart();
		counter = new CounterState();
	});

	afterEach(() => {
		vi.clearAllMocks();
	});

	it('initializes with default state values', () => {
		expect(counter.isCameraActive).toBe(true);
		expect(counter.isCameraCollapsed).toBe(false);
		expect(counter.isSearchOpen).toBe(false);
		expect(counter.isWeightModalOpen).toBe(false);
		expect(counter.isCheckoutOpen).toBe(false);
		expect(counter.isClearConfirmOpen).toBe(false);
		expect(counter.notification).toBeNull();
	});

	it('toggles camera active and collapsed states', () => {
		counter.toggleCamera();
		expect(counter.isCameraActive).toBe(false);

		counter.activateCamera();
		expect(counter.isCameraActive).toBe(true);

		counter.toggleCameraCollapse();
		expect(counter.isCameraCollapsed).toBe(true);
		counter.toggleCameraCollapse();
		expect(counter.isCameraCollapsed).toBe(false);
	});

	it('manages notifications with auto-dismiss and manual dismiss', () => {
		vi.useFakeTimers();
		try {
			counter.showNotification('Test message', 'success', 2000);
			expect(counter.notification).toEqual({
				message: 'Test message',
				type: 'success',
			});

			vi.advanceTimersByTime(2000);
			expect(counter.notification).toBeNull();

			counter.showNotification('Dismiss me', 'info');
			expect(counter.notification?.message).toBe('Dismiss me');
			counter.dismissNotification();
			expect(counter.notification).toBeNull();
		} finally {
			vi.useRealTimers();
		}
	});

	it('opens and closes search, checkout, and clear confirmation dialogs', () => {
		counter.openSearch();
		expect(counter.isSearchOpen).toBe(true);
		counter.closeSearch();
		expect(counter.isSearchOpen).toBe(false);

		counter.openCheckout();
		expect(counter.isCheckoutOpen).toBe(true);
		counter.closeCheckout();
		expect(counter.isCheckoutOpen).toBe(false);

		counter.openClearConfirm();
		expect(counter.isClearConfirmOpen).toBe(true);
		counter.closeClearConfirm();
		expect(counter.isClearConfirmOpen).toBe(false);
	});

	it('handles discrete product selection directly adding to cart', () => {
		counter.handleProductSelect(mockDiscrete);
		expect(cart.items.length).toBe(1);
		expect(cart.items[0].product.id).toBe(mockDiscrete.id);
		expect(counter.notification?.message).toContain(mockDiscrete.name);
	});

	it('handles bulk product selection by prompting weight modal', () => {
		counter.handleProductSelect(mockProduct);
		expect(counter.isWeightModalOpen).toBe(true);
		expect(counter.activeWeightProduct?.id).toBe(mockProduct.id);
		expect(counter.initialWeightGrams).toBe(100);
		expect(cart.items.length).toBe(0);

		// Confirm weight 250g
		counter.handleWeightConfirm(250);
		expect(counter.isWeightModalOpen).toBe(false);
		expect(cart.items.length).toBe(1);
		expect(cart.items[0].weightGrams).toBe(250);
	});

	it('edits weight for existing bulk cart item', () => {
		cart.addItem(mockProduct, { weightGrams: 200 });
		const item = cart.items[0];

		counter.handleEditItemWeight(item);
		expect(counter.isWeightModalOpen).toBe(true);
		expect(counter.activeWeightItemId).toBe(item.id);
		expect(counter.initialWeightGrams).toBe(200);

		// Update to 350g
		counter.handleWeightConfirm(350);
		expect(counter.isWeightModalOpen).toBe(false);
		expect(cart.items[0].weightGrams).toBe(350);
	});

	it('handles clearing cart and checkout completion', () => {
		cart.addItem(mockDiscrete);
		expect(cart.items.length).toBe(1);

		counter.handleClearCart();
		expect(cart.items.length).toBe(0);
		expect(counter.isClearConfirmOpen).toBe(false);
		expect(counter.notification?.message).toBe('Carrito vaciado');

		cart.addItem(mockDiscrete);
		counter.handleCheckoutSuccess();
		expect(cart.items.length).toBe(0);
	});

	it('coordinates barcode scan for discrete item', async () => {
		await counter.handleScan('DISC-20', [mockDiscrete]);
		expect(cart.items.length).toBe(1);
		expect(counter.notification?.message).toContain(mockDiscrete.name);
	});

	it('coordinates barcode scan for bulk item requiring manual weight', async () => {
		await counter.handleScan('ALM-100', [mockProduct]);
		expect(counter.isWeightModalOpen).toBe(true);
		expect(counter.activeWeightProduct?.id).toBe(mockProduct.id);
	});
});
