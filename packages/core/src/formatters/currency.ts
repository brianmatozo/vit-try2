/**
 * Formats an integer amount in whole Argentine Pesos (ARS).
 * Centavos/cents are strictly omitted per domain specification.
 *
 * Example: 1500 -> "$ 1.500"
 */
export function formatARS(
	amount: number,
	options: { space?: boolean } = { space: true },
): string {
	const integerAmount = Math.round(amount);
	const formatted = new Intl.NumberFormat('es-AR', {
		maximumFractionDigits: 0,
		minimumFractionDigits: 0,
	}).format(integerAmount);

	return options.space ? `$ ${formatted}` : `$${formatted}`;
}

/**
 * Parses a user input string into whole Argentine Pesos integer.
 */
export function parseARS(input: string): number {
	const clean = input.replace(/[^\d-]/g, '');
	if (!clean || clean === '-') return 0;
	return Number.parseInt(clean, 10);
}
