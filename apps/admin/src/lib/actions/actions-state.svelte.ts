import type {
	InventoryLedgerResponse,
	ProductResponse,
	ShrinkageMermaRequest,
	StockAdjustmentRequest,
	StockReceivingRequest,
} from '@vitalcer/api';

export interface ActionSuccessBanner {
	title: string;
	description: string;
	ledger?: InventoryLedgerResponse;
}

export class StockActionsState {
	products = $state<ProductResponse[]>([]);

	// Modal states
	isReceiveOpen = $state(false);
	isMermaOpen = $state(false);
	isAdjustOpen = $state(false);

	// Feedback banners
	successBanner = $state<ActionSuccessBanner | null>(null);
	errorMessage = $state<string | null>(null);

	// Form 1: Inbound Receiving
	receiveProductId = $state<number | ''>('');
	receiveQuantity = $state<number | ''>('');
	receiveReferenceId = $state('');
	receiveNotes = $state('');

	// Form 2: Shrinkage / Merma
	mermaProductId = $state<number | ''>('');
	mermaQuantity = $state<number | ''>('');
	mermaNotes = $state('');
	mermaReferenceId = $state('');

	// Form 3: Manual Stock Reconciliation
	adjustProductId = $state<number | ''>('');
	adjustCountedStock = $state<number | ''>('');
	adjustNotes = $state('');
	adjustReferenceId = $state('');

	// Derived helpers
	selectedReceiveProduct = $derived(
		this.products.find((p) => p.id === Number(this.receiveProductId)),
	);

	selectedMermaProduct = $derived(
		this.products.find((p) => p.id === Number(this.mermaProductId)),
	);

	selectedAdjustProduct = $derived(
		this.products.find((p) => p.id === Number(this.adjustProductId)),
	);

	calculatedAdjustmentDelta = $derived.by(() => {
		if (
			!this.selectedAdjustProduct ||
			this.adjustCountedStock === '' ||
			Number.isNaN(Number(this.adjustCountedStock))
		) {
			return null;
		}
		return (
			Number(this.adjustCountedStock) - this.selectedAdjustProduct.current_stock
		);
	});

	openReceive(): void {
		this.errorMessage = null;
		this.isReceiveOpen = true;
	}

	closeReceive(): void {
		this.isReceiveOpen = false;
	}

	openMerma(): void {
		this.errorMessage = null;
		this.isMermaOpen = true;
	}

	closeMerma(): void {
		this.isMermaOpen = false;
	}

	openAdjust(): void {
		this.errorMessage = null;
		this.isAdjustOpen = true;
	}

	closeAdjust(): void {
		this.isAdjustOpen = false;
	}

	validateReceive(): boolean {
		this.errorMessage = null;
		if (
			!this.receiveProductId ||
			!this.receiveQuantity ||
			Number(this.receiveQuantity) <= 0
		) {
			this.errorMessage =
				'Debes seleccionar un producto e ingresar una cantidad mayor a cero.';
			return false;
		}
		return true;
	}

	validateMerma(): boolean {
		this.errorMessage = null;
		if (
			!this.mermaProductId ||
			!this.mermaQuantity ||
			Number(this.mermaQuantity) <= 0 ||
			!this.mermaNotes.trim()
		) {
			this.errorMessage =
				'Debes especificar producto, cantidad mayor a 0 y el motivo obligatorio.';
			return false;
		}
		return true;
	}

	validateAdjust(): boolean {
		this.errorMessage = null;
		if (
			!this.adjustProductId ||
			this.adjustCountedStock === '' ||
			Number(this.adjustCountedStock) < 0 ||
			!this.adjustNotes.trim()
		) {
			this.errorMessage =
				'Debes ingresar el conteo físico (>= 0) y el motivo del ajuste.';
			return false;
		}
		return true;
	}

	buildReceivePayload(): StockReceivingRequest {
		return {
			product_id: Number(this.receiveProductId),
			quantity: Number(this.receiveQuantity),
			reference_id: this.receiveReferenceId.trim() || null,
			notes: this.receiveNotes.trim() || null,
		};
	}

	buildMermaPayload(): ShrinkageMermaRequest {
		return {
			product_id: Number(this.mermaProductId),
			quantity: Number(this.mermaQuantity),
			notes: this.mermaNotes.trim(),
			reference_id: this.mermaReferenceId.trim() || null,
		};
	}

	buildAdjustPayload(): StockAdjustmentRequest {
		return {
			product_id: Number(this.adjustProductId),
			counted_stock: Number(this.adjustCountedStock),
			notes: this.adjustNotes.trim(),
			reference_id: this.adjustReferenceId.trim() || null,
		};
	}

	resetReceive(): void {
		this.receiveProductId = '';
		this.receiveQuantity = '';
		this.receiveReferenceId = '';
		this.receiveNotes = '';
	}

	resetMerma(): void {
		this.mermaProductId = '';
		this.mermaQuantity = '';
		this.mermaNotes = '';
		this.mermaReferenceId = '';
	}

	resetAdjust(): void {
		this.adjustProductId = '';
		this.adjustCountedStock = '';
		this.adjustNotes = '';
		this.adjustReferenceId = '';
	}

	notifySuccess(
		title: string,
		description: string,
		ledger?: InventoryLedgerResponse,
	): void {
		this.successBanner = { title, description, ledger };
	}

	notifyError(message: string): void {
		this.errorMessage = message;
	}

	dismissSuccess(): void {
		this.successBanner = null;
	}

	dismissError(): void {
		this.errorMessage = null;
	}
}
