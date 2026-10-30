import { calculateDiscrepancy, type DiscrepancyStatus } from '@vitalcer/core';

export interface DiscrepancyBadgeInfo {
	label: string;
	variant: 'default' | 'success' | 'warning' | 'destructive' | 'outline';
	amount: number;
	status: DiscrepancyStatus;
}

/**
 * Computes presentation badge information for a financial discrepancy.
 */
export function getDiscrepancyBadgeInfo(
	expectedCash: number,
	actualCash: number | null | undefined,
): DiscrepancyBadgeInfo {
	if (actualCash === null || actualCash === undefined) {
		return {
			label: 'Sin Arqueo',
			variant: 'default',
			amount: 0,
			status: 'exact',
		};
	}

	const result = calculateDiscrepancy(expectedCash, actualCash);

	if (result.status === 'exact') {
		return {
			label: 'Exacto ($0)',
			variant: 'success',
			amount: 0,
			status: 'exact',
		};
	}

	if (result.status === 'surplus') {
		return {
			label: `Sobrante (+$${result.discrepancy.toLocaleString('es-AR')})`,
			variant: 'warning',
			amount: result.discrepancy,
			status: 'surplus',
		};
	}

	return {
		label: `Faltante (-$${Math.abs(result.discrepancy).toLocaleString('es-AR')})`,
		variant: 'destructive',
		amount: result.discrepancy,
		status: 'shortage',
	};
}

/**
 * Formats an ISO UTC date string into Argentine local time display.
 */
export function formatClosureDateTime(
	isoString: string | null | undefined,
): string {
	if (!isoString) return '—';
	try {
		const date = new Date(isoString);
		return new Intl.DateTimeFormat('es-AR', {
			day: '2-digit',
			month: '2-digit',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit',
			hour12: false,
		}).format(date);
	} catch {
		return isoString;
	}
}

/**
 * Formats whole ARS currency without cents.
 */
export function formatCurrencyARS(amount: number | null | undefined): string {
	const safeAmount = Math.round(amount || 0);
	return `$${safeAmount.toLocaleString('es-AR')}`;
}

/**
 * Returns human-readable label and variant for closure status.
 */
export function getClosureStatusBadge(
	status: string | null | undefined,
	autoClosed?: boolean,
): {
	label: string;
	variant: 'default' | 'success' | 'warning' | 'destructive' | 'outline';
} {
	if (status === 'open') {
		return { label: 'Abierta', variant: 'success' };
	}
	if (autoClosed) {
		return { label: 'Auto-Cerrada (20:30)', variant: 'warning' };
	}
	return { label: 'Cerrada', variant: 'default' };
}
