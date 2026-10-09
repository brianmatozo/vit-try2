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

	it('parses real-world 13-digit embedded scale barcode with price', () => {
		// 20 (prefix) 2126 (PLU) 014400 ($14.400 ARS) 4 (check digit)
		const result = parseBarcode('2021260144004');
		expect(result.isEmbeddedScale).toBe(true);
		expect(result.isEmbeddedPrice).toBe(true);
		expect(result.isEmbeddedWeight).toBe(true);
		expect(result.skuOrPlu).toBe('2126');
		expect(result.embeddedPriceWholeArs).toBe(14400);
		expect(result.weightGrams).toBeUndefined();
		expect(result.rawBarcode).toBe('2021260144004');
	});

	it('recognizes all supported in-store prefixes with 13-digit scale barcodes', () => {
		for (const prefix of ['20', '21', '28', '29']) {
			// Prefix + PLU(9999) + Price(015000 = $15.000) + dummy check(0)
			const result = parseBarcode(`${prefix}99990150000`);
			expect(result.isEmbeddedScale).toBe(true);
			expect(result.isEmbeddedPrice).toBe(true);
			expect(result.isEmbeddedWeight).toBe(true);
			expect(result.skuOrPlu).toBe('9999');
			expect(result.embeddedPriceWholeArs).toBe(15000);
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
