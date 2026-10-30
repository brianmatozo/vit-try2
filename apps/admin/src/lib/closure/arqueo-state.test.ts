import { describe, expect, it } from 'vitest';
import { ArqueoState } from './arqueo-state.svelte.js';

describe('ArqueoState', () => {
	it('initializes with all denominations at 0', () => {
		const state = new ArqueoState(50000);
		expect(state.expectedCash).toBe(50000);
		expect(state.totalCounted).toBe(0);
		expect(state.counts[20000]).toBe(0);
		expect(state.counts[10000]).toBe(0);
		expect(state.counts[1000]).toBe(0);
		expect(state.hasDiscrepancy).toBe(true);
		expect(state.discrepancyResult.status).toBe('shortage');
		expect(state.discrepancyResult.discrepancy).toBe(-50000);
	});

	it('computes totalCounted accurately with increments', () => {
		const state = new ArqueoState(45000);
		state.incrementDenom(20000, 2); // 40,000
		state.incrementDenom(2000, 2); // 4,000
		state.incrementDenom(1000, 1); // 1,000
		state.setCoins(200); // 200

		expect(state.totalCounted).toBe(45200);
		expect(state.discrepancyResult.status).toBe('surplus');
		expect(state.discrepancyResult.discrepancy).toBe(200);
	});

	it('decrements cleanly without going below zero', () => {
		const state = new ArqueoState(10000);
		state.incrementDenom(10000, 1);
		expect(state.totalCounted).toBe(10000);

		state.decrementDenom(10000, 2);
		expect(state.counts[10000]).toBe(0);
		expect(state.totalCounted).toBe(0);
	});

	it('detects exact match', () => {
		const state = new ArqueoState(30000);
		state.setDenomCount(10000, 3);
		expect(state.totalCounted).toBe(30000);
		expect(state.hasDiscrepancy).toBe(false);
		expect(state.discrepancyResult.status).toBe('exact');
		expect(state.discrepancyResult.discrepancy).toBe(0);
	});

	it('resets state correctly', () => {
		const state = new ArqueoState(30000);
		state.setDenomCount(10000, 3);
		state.setCoins(500);
		state.notes = 'Some note';

		state.reset(20000);
		expect(state.totalCounted).toBe(0);
		expect(state.coins).toBe(0);
		expect(state.notes).toBe('');
		expect(state.expectedCash).toBe(20000);
	});
});
