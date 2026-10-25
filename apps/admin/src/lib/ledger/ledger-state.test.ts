import { describe, expect, it } from 'vitest';
import { LedgerState } from './ledger-state.svelte';

describe('LedgerState', () => {
	it('initializes with default empty state', () => {
		const state = new LedgerState();
		expect(state.productIdInput).toBe('');
		expect(state.selectedMovementType).toBe('');
		expect(state.activeProductId).toBeUndefined();
		expect(state.hasActiveFilters).toBe(false);
		expect(state.sorting).toEqual([{ id: 'id', desc: true }]);
	});

	it('initializes with initialProductId parameter', () => {
		const state = new LedgerState('42');
		expect(state.productIdInput).toBe('42');
		expect(state.activeProductId).toBe(42);
		expect(state.hasActiveFilters).toBe(true);
	});

	it('correctly derives activeProductId from string inputs', () => {
		const state = new LedgerState();

		state.setProductId('');
		expect(state.activeProductId).toBeUndefined();

		state.setProductId('   ');
		expect(state.activeProductId).toBeUndefined();

		state.setProductId('0');
		expect(state.activeProductId).toBeUndefined();

		state.setProductId('-10');
		expect(state.activeProductId).toBeUndefined();

		state.setProductId('invalid');
		expect(state.activeProductId).toBeUndefined();

		state.setProductId('15');
		expect(state.activeProductId).toBe(15);

		state.setProductId('  99  ');
		expect(state.activeProductId).toBe(99);
	});

	it('updates movement type and derives hasActiveFilters', () => {
		const state = new LedgerState();
		expect(state.hasActiveFilters).toBe(false);

		state.setMovementType('sale_pos');
		expect(state.selectedMovementType).toBe('sale_pos');
		expect(state.hasActiveFilters).toBe(true);
	});

	it('clears product ID and resets all filters', () => {
		const state = new LedgerState('123');
		state.setMovementType('receiving');
		expect(state.hasActiveFilters).toBe(true);

		state.clearProductId();
		expect(state.productIdInput).toBe('');
		expect(state.activeProductId).toBeUndefined();
		expect(state.selectedMovementType).toBe('receiving');

		state.resetFilters();
		expect(state.productIdInput).toBe('');
		expect(state.selectedMovementType).toBe('');
		expect(state.hasActiveFilters).toBe(false);
	});
});
