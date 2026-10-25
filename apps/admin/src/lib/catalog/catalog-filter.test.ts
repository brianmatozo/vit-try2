import type { ProductResponse } from '@vitalcer/api';
import { describe, expect, it } from 'vitest';
import { calculateCatalogMetrics, filterProducts } from './catalog-filter';

const mockProducts: ProductResponse[] = [
	{
		id: 1,
		sku: '7791234567890',
		name: 'Alfajor Choco Diet',
		product_type: 'discrete',
		unit_price: 1500,
		current_stock: 25,
		reserved_stock: 0,
		virtual_stock: 25,
		is_active: true,
		created_at: '2026-01-01T00:00:00Z',
		updated_at: '2026-01-01T00:00:00Z',
	},
	{
		id: 2,
		sku: 'ALM-01',
		plu_code: '0142',
		name: 'Almendras Nonpareil',
		product_type: 'bulk',
		bulk_reference_grams: 100,
		unit_price: 2400,
		current_stock: 5000,
		reserved_stock: 500,
		virtual_stock: 4500,
		is_active: true,
		created_at: '2026-01-01T00:00:00Z',
		updated_at: '2026-01-01T00:00:00Z',
	},
	{
		id: 3,
		sku: 'NUEZ-01',
		plu_code: '0150',
		name: 'Nueces Chandler',
		product_type: 'bulk',
		bulk_reference_grams: 100,
		unit_price: 2200,
		current_stock: 0,
		reserved_stock: 0,
		virtual_stock: 0,
		is_active: false,
		created_at: '2026-01-01T00:00:00Z',
		updated_at: '2026-01-01T00:00:00Z',
	},
	{
		id: 4,
		sku: 'GAL-01',
		name: 'Galletas de Avena',
		product_type: 'discrete',
		unit_price: 1800,
		current_stock: -2,
		reserved_stock: 0,
		virtual_stock: -2,
		is_active: true,
		created_at: '2026-01-01T00:00:00Z',
		updated_at: '2026-01-01T00:00:00Z',
	},
];

describe('filterProducts', () => {
	it('returns all products when search term is empty or whitespace', () => {
		expect(filterProducts(mockProducts, '')).toEqual(mockProducts);
		expect(filterProducts(mockProducts, '   ')).toEqual(mockProducts);
	});

	it('filters by case-insensitive name substring', () => {
		const result = filterProducts(mockProducts, 'choco');
		expect(result).toHaveLength(1);
		expect(result[0].id).toBe(1);
	});

	it('filters by SKU', () => {
		const result = filterProducts(mockProducts, 'alm-01');
		expect(result).toHaveLength(1);
		expect(result[0].id).toBe(2);
	});

	it('filters by PLU code', () => {
		const result = filterProducts(mockProducts, '0150');
		expect(result).toHaveLength(1);
		expect(result[0].id).toBe(3);
	});

	it('matches embedded-weight GS1 scale barcode with matching PLU', () => {
		// Barcode prefix 20 + PLU 0142 + weight 00500 + check digit 8
		const scaleBarcode = '200142005008';
		const result = filterProducts(mockProducts, scaleBarcode);
		expect(result).toHaveLength(1);
		expect(result[0].id).toBe(2);
	});

	it('returns empty array when no product matches', () => {
		expect(filterProducts(mockProducts, 'nonexistent')).toEqual([]);
	});
});

describe('calculateCatalogMetrics', () => {
	it('calculates total, bulk, discrete, and lowStock products correctly', () => {
		const metrics = calculateCatalogMetrics(mockProducts);
		expect(metrics).toEqual({
			total: 4,
			bulk: 2,
			discrete: 2,
			lowStock: 2, // prod-3 (stock 0) and prod-4 (stock -2)
		});
	});

	it('handles empty product list', () => {
		expect(calculateCatalogMetrics([])).toEqual({
			total: 0,
			bulk: 0,
			discrete: 0,
			lowStock: 0,
		});
	});
});
