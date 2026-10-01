/**
 * Formats weight in grams into human-readable string.
 * Examples:
 * - 350 -> "350 g"
 * - 1200 -> "1,2 kg"
 * - 1000 -> "1 kg"
 */
export function formatWeight(grams: number): string {
	if (grams >= 1000) {
		const kg = grams / 1000;
		const formatted = new Intl.NumberFormat('es-AR', {
			maximumFractionDigits: 3,
			minimumFractionDigits: 0,
		}).format(kg);
		return `${formatted} kg`;
	}
	return `${Math.round(grams)} g`;
}
