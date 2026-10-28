import type { RemitoResponse } from '@vitalcer/api';
import { beforeEach, describe, expect, it } from 'vitest';
import { RemitosState } from './remitos-state.svelte';

const MOCK_REMITOS: RemitoResponse[] = [
	{
		id: 1,
		remito_number: 'R-001',
		supplier_name: 'Distribuidora New Day',
		status: 'staged',
		page_count: 1,
		fiscal_blanco_bps: 6000,
		fiscal_negro_bps: 4000,
		iva_rate_bps: 2100,
		total_raw_amount: 50000,
		total_real_amount: 56300,
		created_at: '2026-10-15T10:00:00Z',
		items: [],
	},
	{
		id: 2,
		remito_number: 'R-002',
		supplier_name: 'Patagonia Natural',
		status: 'committed',
		page_count: 2,
		fiscal_blanco_bps: 6000,
		fiscal_negro_bps: 4000,
		iva_rate_bps: 2100,
		total_raw_amount: 100000,
		total_real_amount: 112600,
		created_at: '2026-10-14T10:00:00Z',
		items: [],
	},
];

describe('RemitosState', () => {
	let state: RemitosState;

	beforeEach(() => {
		state = new RemitosState();
		state.remitosList = MOCK_REMITOS;
	});

	it('filters by staged tab by default', () => {
		expect(state.activeTab).toBe('staged');
		expect(state.filteredRemitos.length).toBe(1);
		expect(state.filteredRemitos[0].supplier_name).toBe(
			'Distribuidora New Day',
		);
	});

	it('switches to committed tab', () => {
		state.setTab('committed');
		expect(state.filteredRemitos.length).toBe(1);
		expect(state.filteredRemitos[0].supplier_name).toBe('Patagonia Natural');
	});

	it('shows all remitos on all tab', () => {
		state.setTab('all');
		expect(state.filteredRemitos.length).toBe(2);
	});

	it('filters by supplier name query', () => {
		state.setTab('all');
		state.searchTerm = 'new day';
		expect(state.filteredRemitos.length).toBe(1);
		expect(state.filteredRemitos[0].id).toBe(1);
	});

	it('calculates KPI metrics correctly', () => {
		expect(state.kpis.stagedCount).toBe(1);
		expect(state.kpis.committedCount).toBe(1);
		expect(state.kpis.totalAmountCommitted).toBe(112600);
	});
});
