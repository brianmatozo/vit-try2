import type { RemitoResponse } from '@vitalcer/api';
import { beforeEach, describe, expect, it } from 'vitest';
import { RemitoDetailState } from './remito-detail-state.svelte';

const MOCK_REMITO: RemitoResponse = {
	id: 42,
	remito_number: 'R-0042',
	supplier_name: 'Distribuidora New Day',
	status: 'staged',
	image_paths:
		'["data:image/webp;base64,page1", "data:image/webp;base64,page2"]',
	page_count: 2,
	fiscal_blanco_bps: 6000,
	fiscal_negro_bps: 4000,
	iva_rate_bps: 2100,
	total_raw_amount: 10000,
	total_real_amount: 11260,
	created_at: '2026-10-15T12:00:00Z',
	items: [
		{
			id: 1,
			remito_id: 42,
			line_index: 0,
			raw_description: 'Barrita Almendra x 10 u',
			extracted_quantity: 1,
			extracted_unit_cost: 5000,
			extracted_line_total: 5000,
			product_id: 101,
			multiplier: 10,
			target_unit_type: 'discrete_unit',
			effective_quantity: 1,
			quantity_to_commit: 10,
			calculated_unit_cost: 563,
			match_confidence: 100,
			match_strategy: 'exact_alias',
			is_verified_by_user: true,
		},
		{
			id: 2,
			remito_id: 42,
			line_index: 1,
			raw_description: 'Alfajor Sin Match',
			extracted_quantity: 1,
			extracted_unit_cost: 5000,
			extracted_line_total: 5000,
			product_id: null,
			multiplier: 1,
			target_unit_type: 'discrete_unit',
			effective_quantity: 1,
			quantity_to_commit: 1,
			calculated_unit_cost: 5630,
			match_confidence: 0,
			match_strategy: 'unmatched',
			is_verified_by_user: false,
		},
	],
};

describe('RemitoDetailState', () => {
	let state: RemitoDetailState;

	beforeEach(() => {
		state = new RemitoDetailState();
		state.initFromRemito(MOCK_REMITO);
	});

	it('initializes fiscal split and image list from remito', () => {
		expect(state.fiscalBlancoPct).toBe(60);
		expect(state.fiscalNegroPct).toBe(40);
		expect(state.ivaPct).toBe(21);
		expect(state.imageUrls.length).toBe(2);
		expect(state.activePageIndex).toBe(0);
	});

	it('detects unmatched items and blocks confirmation', () => {
		expect(state.unmatchedCount).toBe(1);
		expect(state.canConfirm).toBe(false);
	});

	it('enables confirmation when all items are matched', () => {
		if (state.remito?.items?.[1]) {
			state.remito.items[1].product_id = 999;
		}
		expect(state.unmatchedCount).toBe(0);
		expect(state.canConfirm).toBe(true);
	});

	it('handles zoom controls', () => {
		expect(state.zoomLevel).toBe(1);
		state.zoomIn();
		expect(state.zoomLevel).toBe(1.25);
		state.zoomOut();
		expect(state.zoomLevel).toBe(1);
		state.resetZoom();
		expect(state.zoomLevel).toBe(1);
	});

	it('calculates line sums and audit discrepancy correctly', () => {
		expect(state.computedLinesSum).toBe(10000);
		expect(state.discrepancyArs).toBe(0);
		expect(state.hasSignificantDiscrepancy).toBe(false);

		// When discrepancy exceeds 1% of total_raw_amount
		if (state.remito) {
			state.remito.total_raw_amount = 9000; // 1000 ARS discrepancy > 90 ARS threshold
		}
		expect(state.discrepancyArs).toBe(1000);
		expect(state.hasSignificantDiscrepancy).toBe(true);
	});

	it('detects low OCR confidence correctly', () => {
		expect(state.isLowConfidence).toBe(false);
		if (state.remito) {
			state.remito.overall_confidence = 35;
		}
		expect(state.isLowConfidence).toBe(true);
	});
});
