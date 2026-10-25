import type { ProductResponse } from '@vitalcer/api';
import { describe, expect, it } from 'vitest';
import { ProductFormState } from './product-form.svelte';

const sampleProduct: ProductResponse = {
	id: 42,
	sku: 'ALM-01',
	name: 'Almendras Nonpareil',
	product_type: 'bulk',
	unit_price: 2400,
	bulk_reference_grams: 100,
	plu_code: '0142',
	current_stock: 3500,
	reserved_stock: 0,
	virtual_stock: 3000,
	min_safety_buffer: 500,
	is_active: true,
	sync_pedidosya: true,
	sync_rappi: false,
	sync_vgo: true,
	sync_mercadolibre: false,
	created_at: '2026-01-01T00:00:00Z',
	updated_at: '2026-01-01T00:00:00Z',
};

describe('ProductFormState', () => {
	it('initializes with default closed state', () => {
		const form = new ProductFormState();
		expect(form.isOpen).toBe(false);
		expect(form.editingProduct).toBeNull();
		expect(form.isEditing).toBe(false);
		expect(form.dialogTitle).toBe('Crear Nuevo Producto');
	});

	it('resets all fields cleanly on openCreate', () => {
		const form = new ProductFormState();
		form.openEdit(sampleProduct);
		expect(form.isEditing).toBe(true);

		form.openCreate();
		expect(form.isOpen).toBe(true);
		expect(form.editingProduct).toBeNull();
		expect(form.isEditing).toBe(false);
		expect(form.sku).toBe('');
		expect(form.name).toBe('');
		expect(form.productType).toBe('discrete');
		expect(form.unitPrice).toBe('');
		expect(form.formError).toBeNull();
	});

	it('populates fields correctly on openEdit', () => {
		const form = new ProductFormState();
		form.openEdit(sampleProduct);

		expect(form.isOpen).toBe(true);
		expect(form.editingProduct).toEqual(sampleProduct);
		expect(form.isEditing).toBe(true);
		expect(form.dialogTitle).toBe('Editar Producto');
		expect(form.sku).toBe('ALM-01');
		expect(form.name).toBe('Almendras Nonpareil');
		expect(form.productType).toBe('bulk');
		expect(form.unitPrice).toBe(2400);
		expect(form.pluCode).toBe('0142');
		expect(form.syncRappi).toBe(false);
	});

	it('validates required fields and price > 0', () => {
		const form = new ProductFormState();
		form.openCreate();

		expect(form.validate()).toBe(false);
		expect(form.formError).toContain('Completa PLU, nombre y precio');

		form.sku = 'SKU-1';
		expect(form.validate()).toBe(false);

		form.name = 'Test Item';
		expect(form.validate()).toBe(false);

		form.unitPrice = 0;
		expect(form.validate()).toBe(false);

		form.unitPrice = -50;
		expect(form.validate()).toBe(false);

		form.unitPrice = 500;
		expect(form.validate()).toBe(true);
		expect(form.formError).toBeNull();
	});

	it('validates 4-digit numeric PLU for bulk products', () => {
		const form = new ProductFormState();
		form.openCreate();
		form.sku = 'BULK-1';
		form.name = 'Semillas';
		form.productType = 'bulk';
		form.unitPrice = 300;

		// Empty PLU is permitted
		form.pluCode = '';
		expect(form.validate()).toBe(true);

		// Non-4-digit PLU is rejected
		form.pluCode = '12';
		expect(form.validate()).toBe(false);
		expect(form.formError).toContain('4 dígitos');

		form.pluCode = 'abcd';
		expect(form.validate()).toBe(false);

		form.pluCode = '12345';
		expect(form.validate()).toBe(false);

		// Valid 4-digit PLU is accepted
		form.pluCode = '0142';
		expect(form.validate()).toBe(true);
		expect(form.formError).toBeNull();
	});

	it('builds valid create and update payloads with whole ARS integers', () => {
		const form = new ProductFormState();
		form.openCreate();
		form.sku = '  ALF-01  ';
		form.name = '  Alfajor Blanco  ';
		form.productType = 'discrete';
		form.unitPrice = 1250.7; // Test whole ARS rounding
		form.initialStock = 10;
		form.minSafetyBuffer = 2;

		const createPayload = form.buildCreatePayload();
		expect(createPayload.sku).toBe('ALF-01');
		expect(createPayload.name).toBe('Alfajor Blanco');
		expect(createPayload.unit_price).toBe(1251); // Math.round
		expect(createPayload.current_stock).toBe(10);
		expect(createPayload.min_safety_buffer).toBe(2);

		form.openEdit(sampleProduct);
		form.unitPrice = 2499.4;
		const updatePayload = form.buildUpdatePayload();
		expect(updatePayload.unit_price).toBe(2499);
		expect(updatePayload.sku).toBe('ALM-01');
	});
});
