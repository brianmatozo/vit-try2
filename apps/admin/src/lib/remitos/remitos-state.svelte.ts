import type { RemitoResponse } from '@vitalcer/api';

export type RemitoTab = 'staged' | 'committed' | 'all';

export interface RemitoKpis {
	stagedCount: number;
	committedCount: number;
	totalAmountCommitted: number;
}

export class RemitosState {
	searchTerm = $state('');
	activeTab = $state<RemitoTab>('staged');
	remitosList = $state<RemitoResponse[]>([]);

	filteredRemitos = $derived.by<RemitoResponse[]>(() => {
		const term = this.searchTerm.trim().toLowerCase();
		return this.remitosList.filter((r) => {
			// Tab filtering
			if (this.activeTab === 'staged' && r.status !== 'staged') return false;
			if (this.activeTab === 'committed' && r.status !== 'committed')
				return false;

			// Search filtering
			if (!term) return true;
			const supplier = (r.supplier_name || '').toLowerCase();
			const number = (r.remito_number || '').toLowerCase();
			return supplier.includes(term) || number.includes(term);
		});
	});

	kpis = $derived.by<RemitoKpis>(() => {
		let stagedCount = 0;
		let committedCount = 0;
		let totalAmountCommitted = 0;

		for (const r of this.remitosList) {
			if (r.status === 'staged') stagedCount += 1;
			if (r.status === 'committed') {
				committedCount += 1;
				totalAmountCommitted += r.total_real_amount || 0;
			}
		}

		return {
			stagedCount,
			committedCount,
			totalAmountCommitted,
		};
	});

	setTab(tab: RemitoTab): void {
		this.activeTab = tab;
	}

	clearSearch(): void {
		this.searchTerm = '';
	}
}
