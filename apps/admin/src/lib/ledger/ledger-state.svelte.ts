import type { SortingState } from '@tanstack/svelte-table';

export class LedgerState {
	productIdInput = $state('');
	selectedMovementType = $state<string>('');
	sorting = $state<SortingState>([{ id: 'id', desc: true }]);

	constructor(initialProductId?: string | null) {
		if (initialProductId) {
			this.productIdInput = initialProductId;
		}
	}

	activeProductId = $derived.by<number | undefined>(() => {
		const num = Number(this.productIdInput.trim());
		return !Number.isNaN(num) && num > 0 ? num : undefined;
	});

	hasActiveFilters = $derived.by<boolean>(() => {
		return !!this.activeProductId || !!this.selectedMovementType;
	});

	setProductId(id: number | string): void {
		this.productIdInput = String(id);
	}

	clearProductId(): void {
		this.productIdInput = '';
	}

	setMovementType(type: string): void {
		this.selectedMovementType = type;
	}

	resetFilters(): void {
		this.productIdInput = '';
		this.selectedMovementType = '';
	}
}
