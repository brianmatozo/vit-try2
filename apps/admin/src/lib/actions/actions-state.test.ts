import type { ProductResponse } from '@vitalcer/api';
import { describe, expect, it } from 'vitest';
import { StockActionsState } from './actions-state.svelte';

const mockProducts: ProductResponse[] = [
	{
		id: 1,
		sku: 'ALF-01',
		name: 'Alfajor Choco',
		product_type: 'discrete',
		unit_price: 1500,
		current_stock: 50,
		reserved_stock: 0,
		virtual_stock: 50,
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
];

describe('StockActionsState', () => {
	it('initializes with all dialogs closed and empty form states', () => {
		const state = new StockActionsState();
		expect(state.isReceiveOpen).toBe(false);
		expect(state.isMermaOpen).toBe(false);
		expect(state.isAdjustOpen).toBe(false);
		expect(state.successBanner).toBeNull();
		expect(state.errorMessage).toBeNull();
	});

	it('resolves derived selected products accurately', () => {
		const state = new StockActionsState();
		state.products = mockProducts;

		state.receiveProductId = 1;
		expect(state.selectedReceiveProduct?.name).toBe('Alfajor Choco');

		state.mermaProductId = 2;
		expect(state.selectedMermaProduct?.name).toBe('Almendras Nonpareil');

		state.adjustProductId = 1;
		expect(state.selectedAdjustProduct?.name).toBe('Alfajor Choco');
	});

	describe('Inbound Receiving', () => {
		it('validates product selection and positive quantity', () => {
			const state = new StockActionsState();
			state.products = mockProducts;

			expect(state.validateReceive()).toBe(false);
			expect(state.errorMessage).toContain('Debes seleccionar un producto');

			state.receiveProductId = 1;
			state.receiveQuantity = 0;
			expect(state.validateReceive()).toBe(false);

			state.receiveQuantity = -10;
			expect(state.validateReceive()).toBe(false);

			state.receiveQuantity = 100;
			expect(state.validateReceive()).toBe(true);
			expect(state.errorMessage).toBeNull();
		});

		it('builds receiving payload and resets form cleanly', () => {
			const state = new StockActionsState();
			state.receiveProductId = 1;
			state.receiveQuantity = 24;
			state.receiveReferenceId = '  REM-9981  ';
			state.receiveNotes = '  Distribuidora Central  ';

			const payload = state.buildReceivePayload();
			expect(payload).toEqual({
				product_id: 1,
				quantity: 24,
				reference_id: 'REM-9981',
				notes: 'Distribuidora Central',
			});

			state.resetReceive();
			expect(state.receiveProductId).toBe('');
			expect(state.receiveQuantity).toBe('');
			expect(state.receiveReferenceId).toBe('');
			expect(state.receiveNotes).toBe('');
		});
	});

	describe('Shrinkage / Merma', () => {
		it('validates product, positive quantity and mandatory justification notes', () => {
			const state = new StockActionsState();
			state.products = mockProducts;

			expect(state.validateMerma()).toBe(false);

			state.mermaProductId = 2;
			state.mermaQuantity = 250;
			// Missing notes
			expect(state.validateMerma()).toBe(false);
			expect(state.errorMessage).toContain('motivo obligatorio');

			state.mermaNotes = '  ';
			expect(state.validateMerma()).toBe(false);

			state.mermaNotes = 'Deshidratación tolva granel';
			expect(state.validateMerma()).toBe(true);
			expect(state.errorMessage).toBeNull();
		});

		it('builds merma payload properly', () => {
			const state = new StockActionsState();
			state.mermaProductId = 2;
			state.mermaQuantity = 150;
			state.mermaNotes = 'Frasco roto';
			state.mermaReferenceId = '';

			const payload = state.buildMermaPayload();
			expect(payload).toEqual({
				product_id: 2,
				quantity: 150,
				notes: 'Frasco roto',
				reference_id: null,
			});
		});
	});

	describe('Stock Reconciliation / Adjustments', () => {
		it('calculates adjustment deltas accurately (positive, zero, negative)', () => {
			const state = new StockActionsState();
			state.products = mockProducts;
			state.adjustProductId = 1; // current_stock is 50

			expect(state.calculatedAdjustmentDelta).toBeNull();

			// Counted 60 -> Delta +10
			state.adjustCountedStock = 60;
			expect(state.calculatedAdjustmentDelta).toBe(10);

			// Counted 50 -> Delta 0
			state.adjustCountedStock = 50;
			expect(state.calculatedAdjustmentDelta).toBe(0);

			// Counted 45 -> Delta -5
			state.adjustCountedStock = 45;
			expect(state.calculatedAdjustmentDelta).toBe(-5);
		});

		it('validates physical counted stock >= 0 and mandatory justification notes', () => {
			const state = new StockActionsState();
			state.products = mockProducts;
			state.adjustProductId = 1;

			expect(state.validateAdjust()).toBe(false);

			state.adjustCountedStock = -1;
			state.adjustNotes = 'Recuento';
			expect(state.validateAdjust()).toBe(false);

			// Counted stock 0 is valid (out of stock reconciliation)
			state.adjustCountedStock = 0;
			state.adjustNotes = '';
			expect(state.validateAdjust()).toBe(false);

			state.adjustNotes = 'Agotado en góndola verificado';
			expect(state.validateAdjust()).toBe(true);
			expect(state.errorMessage).toBeNull();
		});

		it('builds adjustment payload properly', () => {
			const state = new StockActionsState();
			state.adjustProductId = 1;
			state.adjustCountedStock = 40;
			state.adjustNotes = 'Auditoría mensual';
			state.adjustReferenceId = 'AUD-2026-01';

			const payload = state.buildAdjustPayload();
			expect(payload).toEqual({
				product_id: 1,
				counted_stock: 40,
				notes: 'Auditoría mensual',
				reference_id: 'AUD-2026-01',
			});
		});
	});

	describe('Feedback notifications', () => {
		it('manages success and error messages cleanly', () => {
			const state = new StockActionsState();

			state.notifySuccess('Éxito', 'Operación completada');
			expect(state.successBanner?.title).toBe('Éxito');

			state.dismissSuccess();
			expect(state.successBanner).toBeNull();

			state.notifyError('Fallo de red');
			expect(state.errorMessage).toBe('Fallo de red');

			state.dismissError();
			expect(state.errorMessage).toBeNull();
		});
	});
});
