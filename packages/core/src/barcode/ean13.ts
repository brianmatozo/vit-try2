import type { ParsedBarcode } from './types.js';

export const IN_STORE_PREFIXES: ReadonlySet<string> = new Set([
	'20',
	'21',
	'28',
	'29',
]);

/**
 * Calculates the standard GS1 Modulo 10 check digit for a 12-digit number string.
 */
export function calculateEanCheckDigit(digits12: string): number {
	if (digits12.length !== 12 || !/^\d{12}$/.test(digits12)) {
		throw new Error('Expected 12 digit string to calculate EAN check digit');
	}

	let sum = 0;
	for (let i = 0; i < 12; i++) {
		const digit = Number.parseInt(digits12[i], 10);
		// Odd positions (0-indexed: 1, 3, 5, ...) are multiplied by 3, even by 1
		sum += i % 2 === 1 ? digit * 3 : digit;
	}

	const remainder = sum % 10;
	return remainder === 0 ? 0 : 10 - remainder;
}

/**
 * Validates whether a 13-digit string has a valid GS1 check digit.
 */
export function isValidEan13(code: string): boolean {
	if (code.length !== 13 || !/^\d{13}$/.test(code)) {
		return false;
	}
	const expectedCheck = calculateEanCheckDigit(code.substring(0, 12));
	return Number.parseInt(code[12], 10) === expectedCheck;
}

/**
 * Parse raw barcode string into discrete SKU or scale-embedded PLU & weight.
 * Matches backend server/utils/barcode.py behavior:
 * Format: PP IIII WWWWW C (12 or 13 digits)
 * - PP: In-store prefix (20, 21, 28, 29)
 * - IIII: 4-digit PLU code
 * - WWWWW: 5-digit weight in grams
 * - C: Optional check digit
 */
export function parseBarcode(raw: string): ParsedBarcode {
	const clean = raw.trim();

	if ((clean.length === 12 || clean.length === 13) && /^\d+$/.test(clean)) {
		const prefix = clean.substring(0, 2);
		if (IN_STORE_PREFIXES.has(prefix)) {
			const plu = clean.substring(2, 6);
			const weightRaw = clean.substring(6, 11);
			const weightGrams = Number.parseInt(weightRaw, 10);

			return {
				rawBarcode: clean,
				isEmbeddedWeight: true,
				skuOrPlu: plu,
				weightGrams: weightGrams,
			};
		}
	}

	return {
		rawBarcode: clean,
		isEmbeddedWeight: false,
		skuOrPlu: clean,
	};
}
