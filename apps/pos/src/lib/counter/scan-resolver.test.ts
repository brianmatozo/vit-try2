import type { ProductResponse, ScanBarcodeResponse } from '@vitalcer/api';
import { describe, expect, it, vi } from 'vitest';
import { type ApiScanFn, resolveBarcodeScan } from './scan-resolver';

const mockDiscreteProduct: ProductResponse = {
	id: 1,
	sku: 'DISC-001',
	name: 'Galletitas de Avena',
	product_type: 'discrete',
	unit_price: 1500,
	current_stock: 50,
	reserved_stock: 0,
	virtual_stock: 50,
	is_active: true,
	created_at: '2026-01-01T00:00:00Z',
	updated_at: '2026-01-01T00:00:00Z',
};

const mockBulkProduct: ProductResponse = {
	id: 2,
	sku: 'BULK-001',
	plu_code: '1234',
	name: 'Nueces Mariposa',
	product_type: 'bulk',
	unit_price: 4500,
	bulk_reference_grams: 100,
	current_stock: 20000,
	reserved_stock: 0,
	virtual_stock: 20000,
	is_active: true,
	created_at: '2026-01-01T00:00:00Z',
	updated_at: '2026-01-01T00:00:00Z',
};

const mockCatalog: ProductResponse[] = [mockDiscreteProduct, mockBulkProduct];

describe('resolveBarcodeScan', () => {
	it('returns null for empty or whitespace barcodes', async () => {
		const res1 = await resolveBarcodeScan('', mockCatalog);
		const res2 = await resolveBarcodeScan('   ', mockCatalog);
		expect(res1).toBeNull();
		expect(res2).toBeNull();
	});

	it('resolves discrete product from client catalog', async () => {
		const res = await resolveBarcodeScan('DISC-001', mockCatalog);
		expect(res).toEqual({
			type: 'add_to_cart',
			product: mockDiscreteProduct,
			options: {
				weightGrams: undefined,
				lineTotal: undefined,
				rawBarcode: 'DISC-001',
			},
		});
	});

	it('prompts weight for bulk product scanned by SKU or PLU without embedded weight', async () => {
		const res = await resolveBarcodeScan('1234', mockCatalog);
		expect(res).toEqual({
			type: 'prompt_weight',
			product: mockBulkProduct,
			initialWeightGrams: 100,
		});
	});

	it('resolves GS1 embedded-scale barcode (20 + 4-digit PLU + price)', async () => {
		// Mock bulk product: $4,500 ARS per 100g
		// 500g costs: 5 * $4,500 = $22,500 ARS
		// 13-digit scale barcode format: 20 + 1234 (PLU) + 022500 (price) + check digit
		const res = await resolveBarcodeScan('2012340225000', mockCatalog);
		expect(res?.type).toBe('add_to_cart');
		if (res?.type === 'add_to_cart') {
			expect(res.product.id).toBe(mockBulkProduct.id);
			expect(res.options.weightGrams).toBe(500);
			expect(res.options.lineTotal).toBe(22500);
		}
	});

	it('resolves product via fallback API when not found in local catalog', async () => {
		const serverProduct: ProductResponse = {
			id: 3,
			sku: 'SRV-001',
			name: 'Té Verde Orgánico',
			product_type: 'discrete',
			unit_price: 2200,
			current_stock: 15,
			reserved_stock: 0,
			virtual_stock: 15,
			is_active: true,
			created_at: '2026-01-01T00:00:00Z',
			updated_at: '2026-01-01T00:00:00Z',
		};

		const mockApi: ApiScanFn = vi.fn().mockResolvedValue({
			data: {
				barcode: 'SRV-001',
				raw_barcode: 'SRV-001',
				is_embedded_weight: false,
				product: serverProduct,
				quantity: 1,
				line_total: 2200,
			} as ScanBarcodeResponse,
		});

		const res = await resolveBarcodeScan('SRV-001', [], mockApi);
		expect(res).toEqual({
			type: 'add_to_cart',
			product: serverProduct,
			options: {
				weightGrams: undefined,
				lineTotal: 2200,
				rawBarcode: 'SRV-001',
			},
		});
	});

	it('prompts weight if fallback API returns bulk product without embedded weight', async () => {
		const serverBulk: ProductResponse = {
			...mockBulkProduct,
			id: 99,
		};

		const mockApi: ApiScanFn = vi.fn().mockResolvedValue({
			data: {
				barcode: 'BULK-99',
				raw_barcode: 'BULK-99',
				is_embedded_weight: false,
				product: serverBulk,
				quantity: 1,
				line_total: 4500,
			} as ScanBarcodeResponse,
		});

		const res = await resolveBarcodeScan('BULK-99', [], mockApi);
		expect(res).toEqual({
			type: 'prompt_weight',
			product: serverBulk,
			initialWeightGrams: 100,
		});
	});

	it('returns error when fallback API reports product not found', async () => {
		const mockApi: ApiScanFn = vi.fn().mockResolvedValue({
			error: { detail: 'Producto no encontrado' },
		});

		const res = await resolveBarcodeScan('UNKNOWN-123', [], mockApi);
		expect(res).toEqual({
			type: 'error',
			message: 'Producto no encontrado',
		});
	});

	it('handles network or unexpected exceptions gracefully', async () => {
		const mockApi: ApiScanFn = vi
			.fn()
			.mockRejectedValue(new Error('Network offline'));

		const res = await resolveBarcodeScan('OFFLINE-123', [], mockApi);
		expect(res).toEqual({
			type: 'error',
			message: 'Código no encontrado: OFFLINE-123',
		});
	});
});
