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
