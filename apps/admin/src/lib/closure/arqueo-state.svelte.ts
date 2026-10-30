import {
	ARGENTINE_BANKNOTES,
	type BanknoteDenomination,
	calculateCashCount,
	calculateDiscrepancy,
	type DenominationBreakdown,
	type DiscrepancyResult,
} from '@vitalcer/core';

export class ArqueoState {
	counts = $state<DenominationBreakdown>({});
	coins = $state<number>(0);
	expectedCash = $state<number>(0);
	notes = $state<string>('');

	constructor(expectedCash = 0) {
		this.expectedCash = expectedCash;
		this.reset();
	}

	reset(newExpected = 0) {
		const initial: DenominationBreakdown = {};
		for (const denom of ARGENTINE_BANKNOTES) {
			initial[denom] = 0;
		}
		this.counts = initial;
		this.coins = 0;
		this.notes = '';
		if (newExpected > 0) {
			this.expectedCash = newExpected;
		}
	}

	setExpectedCash(amount: number) {
		this.expectedCash = Math.max(0, Math.round(amount || 0));
	}

	setDenomCount(denom: BanknoteDenomination | number, count: number) {
		const safeCount = Math.max(0, Math.floor(count || 0));
		this.counts = {
			...this.counts,
			[denom]: safeCount,
		};
	}

	incrementDenom(denom: BanknoteDenomination | number, step = 1) {
		const current = this.counts[denom] || 0;
		this.setDenomCount(denom, current + step);
	}

	decrementDenom(denom: BanknoteDenomination | number, step = 1) {
		const current = this.counts[denom] || 0;
		this.setDenomCount(denom, Math.max(0, current - step));
	}

	setCoins(amount: number) {
		this.coins = Math.max(0, Math.floor(amount || 0));
	}

	get totalCounted(): number {
		return calculateCashCount(this.counts, this.coins);
	}

	get discrepancyResult(): DiscrepancyResult {
		return calculateDiscrepancy(this.expectedCash, this.totalCounted);
	}

	get hasDiscrepancy(): boolean {
		return this.discrepancyResult.status !== 'exact';
	}
}
