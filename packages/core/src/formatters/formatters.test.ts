import { describe, expect, it } from 'vitest';
import { formatARS, parseARS } from './currency.js';
import { calculateBulkLineTotal, calculateWeightFromPrice } from './pricing.js';
import { formatWeight } from './weight.js';

describe('Formatters and Calculations', () => {
	describe('formatARS & parseARS', () => {
		it('formats whole Argentine Pesos without centavos', () => {
			const formatted = formatARS(1500);
			expect(formatted).toContain('1.500');
			expect(formatted).not.toContain(',');
		});

		it('handles rounding floating numbers if provided', () => {
			expect(formatARS(1500.4)).toContain('1.500');
			expect(formatARS(1500.8)).toContain('1.501');
		});

		it('parses formatted strings back to integer whole ARS', () => {
			expect(parseARS('$ 1.500')).toBe(1500);
			expect(parseARS('$15.000')).toBe(15000);
			expect(parseARS('')).toBe(0);
		});
	});

	describe('formatWeight', () => {
		it('formats grams under 1000g', () => {
			expect(formatWeight(350)).toBe('350 g');
			expect(formatWeight(50)).toBe('50 g');
		});

		it('formats kg for 1000g and above', () => {
			expect(formatWeight(1000)).toBe('1 kg');
			expect(formatWeight(1500)).toBe('1,5 kg');
			expect(formatWeight(2350)).toBe('2,35 kg');
		});
	});

	describe('calculateBulkLineTotal', () => {
		it('calculates price in whole ARS for weighted goods correctly', () => {
			// 350g almonds @ $1.500 per 100g = (1500 / 100) * 350 = 5250 ARS
			const total = calculateBulkLineTotal(1500, 100, 350);
			expect(total).toBe(5250);
		});

		it('rounds to integer whole ARS', () => {
			// 333g @ $1.000 per 100g = 10 * 333 = 3330
			// 333g @ $1.005 per 100g = 10.05 * 333 = 3346.65 -> 3347
			const total = calculateBulkLineTotal(1005, 100, 333);
			expect(total).toBe(3347);
		});

		it('throws if reference grams is zero or negative', () => {
			expect(() => calculateBulkLineTotal(1000, 0, 100)).toThrow();
		});
	});

	describe('calculateWeightFromPrice', () => {
		it('calculates physical weight from scale embedded price in whole ARS', () => {
			// Nuez x500g: unitPrice = 2880 ARS per 100g, label price = 14400 ARS
			// Weight = (14400 / 2880) * 100 = 500 grams
			const weight = calculateWeightFromPrice(2880, 100, 14400);
			expect(weight).toBe(500);
		});

		it('rounds to nearest integer grams for fractional divisions', () => {
			// 123g @ $2490 / 100g -> scale printed 3063 ARS
			// Reverse: round((3063 / 2490) * 100) = 123g
			const weight = calculateWeightFromPrice(2490, 100, 3063);
			expect(weight).toBe(123);
		});

		it('returns 0 if price or unitPrice is zero or negative', () => {
			expect(calculateWeightFromPrice(0, 100, 14400)).toBe(0);
			expect(calculateWeightFromPrice(2880, 0, 14400)).toBe(0);
		});
	});
});
