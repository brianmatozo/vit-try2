import { describe, expect, it } from 'vitest';
import {
	ARGENTINE_BANKNOTES,
	calculateCashCount,
	calculateDiscrepancy,
} from './denominations.js';

describe('denominations domain', () => {
	it('defines standard Argentine banknotes in descending order', () => {
		expect(ARGENTINE_BANKNOTES).toEqual([
			20000, 10000, 2000, 1000, 500, 200, 100,
		]);
	});

	it('calculates physical cash count from banknote breakdown', () => {
		const breakdown = {
			20000: 2, // 40,000
			10000: 5, // 50,000
			2000: 3, // 6,000
			1000: 10, // 10,000
			500: 4, // 2,000
			200: 5, // 1,000
			100: 8, // 800
		};
		const total = calculateCashCount(breakdown, 250); // +250 coins
		expect(total).toBe(110050);
	});

	it('handles empty breakdown and zero coins safely', () => {
		expect(calculateCashCount({})).toBe(0);
		expect(calculateCashCount({}, 500)).toBe(500);
	});

	it('ignores negative counts or invalid values', () => {
		const breakdown = {
			10000: -2,
			1000: 3,
		};
		expect(calculateCashCount(breakdown, -50)).toBe(3000);
	});

	describe('calculateDiscrepancy', () => {
		it('identifies exact match as exact status', () => {
			const res = calculateDiscrepancy(50000, 50000);
			expect(res).toEqual({ discrepancy: 0, status: 'exact' });
		});

		it('identifies shortage when counted < expected', () => {
			const res = calculateDiscrepancy(50000, 48500);
			expect(res).toEqual({ discrepancy: -1500, status: 'shortage' });
		});

		it('identifies surplus when counted > expected', () => {
			const res = calculateDiscrepancy(50000, 52300);
			expect(res).toEqual({ discrepancy: 2300, status: 'surplus' });
		});
	});
});
