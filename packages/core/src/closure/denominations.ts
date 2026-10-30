/**
 * Argentine Peso banknote denominations in active circulation.
 */
export const ARGENTINE_BANKNOTES = [
	20000, 10000, 2000, 1000, 500, 200, 100,
] as const;

export type BanknoteDenomination = (typeof ARGENTINE_BANKNOTES)[number];

export type DenominationBreakdown = Record<number, number>;

export type DiscrepancyStatus = 'exact' | 'shortage' | 'surplus';

export interface DiscrepancyResult {
	discrepancy: number;
	status: DiscrepancyStatus;
}

/**
 * Calculates total physical cash counted in drawer from bill counts and optional coins.
 */
export function calculateCashCount(
	breakdown: DenominationBreakdown,
	extraCoins = 0,
): number {
	let total = 0;

	for (const [denomStr, count] of Object.entries(breakdown)) {
		const denom = Number(denomStr);
		const safeCount = Math.max(0, Math.floor(count || 0));
		if (!Number.isNaN(denom) && denom > 0) {
			total += denom * safeCount;
		}
	}

	const safeCoins = Math.max(0, Math.floor(extraCoins || 0));
	return Math.round(total + safeCoins);
}

/**
 * Compares counted physical cash against system expected cash to determine discrepancy.
 * Positive = Surplus (sobrante de caja)
 * Negative = Shortage (faltante de caja)
 * Zero = Exact (caja cuadrada)
 */
export function calculateDiscrepancy(
	expectedCash: number,
	countedCash: number,
): DiscrepancyResult {
	const discrepancy = Math.round(countedCash) - Math.round(expectedCash);

	if (discrepancy === 0) {
		return { discrepancy: 0, status: 'exact' };
	}

	if (discrepancy < 0) {
		return { discrepancy, status: 'shortage' };
	}

	return { discrepancy, status: 'surplus' };
}
