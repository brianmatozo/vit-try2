import type { RemitoItemResponse, RemitoResponse } from '@vitalcer/api';

export class RemitoDetailState {
	remito = $state<RemitoResponse | null>(null);
	activePageIndex = $state(0);
	zoomLevel = $state(1);
	isQuickProductOpen = $state(false);
	activeItemForProduct = $state<RemitoItemResponse | null>(null);
	isConfirming = $state(false);
	isRejecting = $state(false);

	fiscalBlancoPct = $state(60);
	fiscalNegroPct = $state(40);
	ivaPct = $state(21);

	imageUrls = $derived.by<string[]>(() => {
		if (!this.remito?.image_paths) return [];
		try {
			const parsed = JSON.parse(this.remito.image_paths);
			return Array.isArray(parsed) ? parsed : [];
		} catch {
			return [];
		}
	});

	unmatchedCount = $derived.by<number>(() => {
		if (!this.remito?.items) return 0;
		return this.remito.items.filter(
			(it) => it.effective_quantity > 0 && !it.product_id,
		).length;
	});

	canConfirm = $derived(
		this.remito?.status === 'staged' &&
			this.unmatchedCount === 0 &&
			!this.isConfirming,
	);

	computedLinesSum = $derived.by<number>(() => {
		if (!this.remito?.items) return 0;
		return this.remito.items.reduce(
			(sum, it) => sum + (it.extracted_line_total || 0),
			0,
		);
	});

	discrepancyArs = $derived.by<number>(() => {
		if (!this.remito) return 0;
		const target = this.remito.total_raw_amount || 0;
		if (target === 0) return 0;
		return Math.abs(this.computedLinesSum - target);
	});

	hasSignificantDiscrepancy = $derived.by<boolean>(() => {
		if (!this.remito?.total_raw_amount) return false;
		const threshold = Math.max(
			Math.floor(this.remito.total_raw_amount * 0.01),
			1,
		);
		return this.discrepancyArs > threshold;
	});

	initFromRemito(r: RemitoResponse): void {
		this.remito = r;
		this.fiscalBlancoPct = Math.round(r.fiscal_blanco_bps / 100);
		this.fiscalNegroPct = Math.round(r.fiscal_negro_bps / 100);
		this.ivaPct = Math.round(r.iva_rate_bps / 100);
		this.activePageIndex = 0;
		this.zoomLevel = 1;
	}

	zoomIn(): void {
		this.zoomLevel = Math.min(this.zoomLevel + 0.25, 3.0);
	}

	zoomOut(): void {
		this.zoomLevel = Math.max(this.zoomLevel - 0.25, 0.75);
	}

	resetZoom(): void {
		this.zoomLevel = 1;
	}

	setPage(index: number): void {
		if (index >= 0 && index < this.imageUrls.length) {
			this.activePageIndex = index;
			this.resetZoom();
		}
	}

	openQuickProduct(item: RemitoItemResponse): void {
		this.activeItemForProduct = item;
		this.isQuickProductOpen = true;
	}

	closeQuickProduct(): void {
		this.isQuickProductOpen = false;
		this.activeItemForProduct = null;
	}

	updateFiscalSplit(blanco: number, negro: number, iva?: number): void {
		this.fiscalBlancoPct = blanco;
		this.fiscalNegroPct = negro;
		if (iva !== undefined) this.ivaPct = iva;
	}
}
