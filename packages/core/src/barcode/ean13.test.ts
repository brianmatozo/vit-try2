import { describe, expect, it } from 'vitest';
import { calculateEanCheckDigit, isValidEan13, parseBarcode } from './ean13.js';

describe('Barcode Parser (EAN-13 scale & retail)', () => {
	it('parses embedded scale barcode with 12 digits', () => {
		// 20 0142 00350 7
		const result = parseBarcode('200142003507');
		expect(result.isEmbeddedWeight).toBe(true);
		expect(result.skuOrPlu).toBe('0142');
		expect(result.weightGrams).toBe(350);
		expect(result.rawBarcode).toBe('200142003507');
	});

	it('parses embedded scale barcode with 13 digits', () => {
		const result = parseBarcode('2001420035070');
		expect(result.isEmbeddedWeight).toBe(true);
		expect(result.skuOrPlu).toBe('0142');
		expect(result.weightGrams).toBe(350);
	});

	it('recognizes all supported in-store prefixes', () => {
		for (const prefix of ['20', '21', '28', '29']) {
			const result = parseBarcode(`${prefix}9999015000`);
			expect(result.isEmbeddedWeight).toBe(true);
			expect(result.skuOrPlu).toBe('9999');
			expect(result.weightGrams).toBe(1500);
		}
	});

	it('parses discrete retail barcodes without embedding weight', () => {
		const result = parseBarcode('7790895000430');
		expect(result.isEmbeddedWeight).toBe(false);
		expect(result.skuOrPlu).toBe('7790895000430');
		expect(result.weightGrams).toBeUndefined();
	});

	it('parses alphanumeric SKUs', () => {
		const result = parseBarcode('COOKIE-OREO-120G');
		expect(result.isEmbeddedWeight).toBe(false);
		expect(result.skuOrPlu).toBe('COOKIE-OREO-120G');
		expect(result.weightGrams).toBeUndefined();
	});

	it('trims whitespace', () => {
		const result = parseBarcode('  200142003507 \n');
		expect(result.isEmbeddedWeight).toBe(true);
		expect(result.skuOrPlu).toBe('0142');
		expect(result.weightGrams).toBe(350);
	});

	it('calculates GS1 EAN check digit correctly', () => {
		// 779089500043 -> check digit 0
		expect(calculateEanCheckDigit('779089500043')).toBe(0);
		expect(isValidEan13('7790895000430')).toBe(true);
	});
});
