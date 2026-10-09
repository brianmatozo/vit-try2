import type { ProductResponse } from '@vitalcer/api';
import { calculateBulkLineTotal } from '@vitalcer/core';

export interface CartItem {
	id: string;
	product: ProductResponse;
	isBulk: boolean;
	quantity: number;
	weightGrams?: number;
	unitPrice: number;
	lineTotal: number;
	rawBarcode?: string;
}

export class CartState {
	items = $state<CartItem[]>([]);

	totalAmount = $derived(
		this.items.reduce((sum, item) => sum + item.lineTotal, 0),
	);

	totalUnits = $derived(
		this.items.reduce((sum, item) => {
			if (item.isBulk) {
				return sum + 1;
			}
			return sum + item.quantity;
		}, 0),
	);

	isEmpty = $derived(this.items.length === 0);

	addItem(
		product: ProductResponse,
		options?: {
			weightGrams?: number;
			lineTotal?: number;
			rawBarcode?: string;
			quantity?: number;
		},
	): CartItem {
		const isBulk = product.product_type === 'bulk';
		const qty = options?.quantity ?? 1;

		if (isBulk) {
			const weightGrams =
				options?.weightGrams ?? product.bulk_reference_grams ?? 100;
			const refGrams =
				product.bulk_reference_grams && product.bulk_reference_grams > 0
					? product.bulk_reference_grams
					: 100;
			const lineTotal =
				options?.lineTotal ??
				calculateBulkLineTotal(product.unit_price, refGrams, weightGrams);

			const newItem: CartItem = {
				id:
					typeof crypto !== 'undefined' && crypto.randomUUID
						? crypto.randomUUID()
						: `item-${Date.now()}-${Math.random()}`,
				product,
				isBulk: true,
				quantity: 1,
				weightGrams,
				unitPrice: product.unit_price,
				lineTotal,
				rawBarcode: options?.rawBarcode,
			};

			this.items.unshift(newItem);
			return newItem;
		}

		// Discrete unit item: check if already exists
		const existingIndex = this.items.findIndex(
			(it) => !it.isBulk && it.product.id === product.id,
		);

		if (existingIndex >= 0) {
			const existing = this.items[existingIndex];
			const newQty = existing.quantity + qty;
			const updated: CartItem = {
				...existing,
				quantity: newQty,
				lineTotal: existing.unitPrice * newQty,
			};
			// Move updated item to top for instant cashier visibility
			this.items.splice(existingIndex, 1);
			this.items.unshift(updated);
			return updated;
		}

		const newItem: CartItem = {
			id:
				typeof crypto !== 'undefined' && crypto.randomUUID
					? crypto.randomUUID()
					: `item-${Date.now()}-${Math.random()}`,
			product,
			isBulk: false,
			quantity: qty,
			unitPrice: product.unit_price,
			lineTotal: product.unit_price * qty,
			rawBarcode: options?.rawBarcode,
		};

		this.items.unshift(newItem);
		return newItem;
	}

	updateQuantity(itemId: string, delta: number) {
		const index = this.items.findIndex((it) => it.id === itemId);
		if (index === -1) return;

		const item = this.items[index];
		if (item.isBulk) return; // bulk items are modified via weight

		const newQty = item.quantity + delta;
		if (newQty <= 0) {
			this.removeItem(itemId);
			return;
		}

		this.items[index] = {
			...item,
			quantity: newQty,
			lineTotal: item.unitPrice * newQty,
		};
	}

	updateWeight(itemId: string, newWeightGrams: number) {
		const index = this.items.findIndex((it) => it.id === itemId);
		if (index === -1) return;

		const item = this.items[index];
		if (!item.isBulk) return;

		const weight = Math.max(1, Math.round(newWeightGrams));
		const refGrams =
			item.product.bulk_reference_grams && item.product.bulk_reference_grams > 0
				? item.product.bulk_reference_grams
				: 100;
		const lineTotal = calculateBulkLineTotal(item.unitPrice, refGrams, weight);

		this.items[index] = {
			...item,
			weightGrams: weight,
			lineTotal,
		};
	}

	removeItem(itemId: string) {
		this.items = this.items.filter((it) => it.id !== itemId);
	}

	clearCart() {
		this.items = [];
	}
}

export const cart = new CartState();
