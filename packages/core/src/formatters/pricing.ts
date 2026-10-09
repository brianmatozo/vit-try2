/**
 * Computes line total for bulk goods sold by weight.
 *
 * All inputs and the output are integers in whole Argentine Pesos (ARS).
 *
 * Example:
 * unitPriceWholeArs = 1500 ($1.500)
 * bulkReferenceGrams = 100 (per 100g)
 * weightGrams = 350
 * Total = (1500 / 100) * 350 = 15 * 350 = 5250 ARS
 */
export function calculateBulkLineTotal(
	unitPriceWholeArs: number,
	bulkReferenceGrams: number,
	weightGrams: number,
): number {
	if (bulkReferenceGrams <= 0) {
		throw new Error('bulkReferenceGrams must be strictly positive');
	}
	return Math.round((unitPriceWholeArs / bulkReferenceGrams) * weightGrams);
}

/**
 * Reverse-calculates physical weight in grams from embedded label price in whole ARS.
 *
 * Example:
 * unitPriceWholeArs = 2880 ($2.880 per 100g)
 * bulkReferenceGrams = 100
 * priceWholeArs = 14400 ($14.400 total label price)
 * Total weight = round((14400 / 2880) * 100) = 500 grams
 */
export function calculateWeightFromPrice(
	unitPriceWholeArs: number,
	bulkReferenceGrams: number,
	priceWholeArs: number,
): number {
	if (unitPriceWholeArs <= 0 || bulkReferenceGrams <= 0) {
		return 0;
	}
	return Math.round((priceWholeArs / unitPriceWholeArs) * bulkReferenceGrams);
}
