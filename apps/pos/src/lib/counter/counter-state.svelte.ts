import type { ProductResponse } from '@vitalcer/api';
import { formatWeight } from '@vitalcer/core';
import { playBeep, playError } from '$lib/audio/sound';
import { type CartItem, cart } from '$lib/cart/cart.svelte';
import { HardwareScannerListener } from './hardware-scanner';
import { type ApiScanFn, resolveBarcodeScan } from './scan-resolver';

export interface CounterNotification {
	message: string;
	type: 'success' | 'error' | 'info';
}

export class CounterState {
	// Scanner view states
	isCameraActive = $state(true);
	isCameraCollapsed = $state(false);

	// Modal states
	isSearchOpen = $state(false);
	isWeightModalOpen = $state(false);
	isCheckoutOpen = $state(false);
	isClearConfirmOpen = $state(false);

	// Bulk weight editing state
	activeWeightProduct = $state<ProductResponse | null>(null);
	activeWeightItemId = $state<string | null>(null);
	initialWeightGrams = $state(100);

	// Notification banner state
	notification = $state<CounterNotification | null>(null);
	private notificationTimer: ReturnType<typeof setTimeout> | null = null;

	// Hardware HID keyboard scanner
	private hardwareScanner: HardwareScannerListener;
	private currentCatalog: ProductResponse[] = [];

	constructor() {
		this.hardwareScanner = new HardwareScannerListener((code) => {
			this.handleScan(code, this.currentCatalog);
		});
	}

	toggleCamera(): void {
		this.isCameraActive = !this.isCameraActive;
	}

	activateCamera(): void {
		this.isCameraActive = true;
	}

	toggleCameraCollapse(): void {
		this.isCameraCollapsed = !this.isCameraCollapsed;
	}

	showNotification(
		message: string,
		type: 'success' | 'error' | 'info' = 'info',
		durationMs = 2800,
	): void {
		if (this.notificationTimer) clearTimeout(this.notificationTimer);
		this.notification = { message, type };
		this.notificationTimer = setTimeout(() => {
			this.notification = null;
		}, durationMs);
	}

	dismissNotification(): void {
		if (this.notificationTimer) clearTimeout(this.notificationTimer);
		this.notification = null;
	}

	openSearch(): void {
		this.isSearchOpen = true;
	}

	closeSearch(): void {
		this.isSearchOpen = false;
	}

	openCheckout(): void {
		this.isCheckoutOpen = true;
	}

	closeCheckout(): void {
		this.isCheckoutOpen = false;
	}

	openClearConfirm(): void {
		this.isClearConfirmOpen = true;
	}

	closeClearConfirm(): void {
		this.isClearConfirmOpen = false;
	}

	openWeightModal(
		product: ProductResponse,
		options?: { itemId?: string; initialWeightGrams?: number },
	): void {
		this.activeWeightProduct = product;
		this.activeWeightItemId = options?.itemId ?? null;
		this.initialWeightGrams =
			options?.initialWeightGrams ?? product.bulk_reference_grams ?? 100;
		this.isWeightModalOpen = true;
	}

	closeWeightModal(): void {
		this.isWeightModalOpen = false;
		this.activeWeightProduct = null;
		this.activeWeightItemId = null;
	}

	async handleScan(
		barcode: string,
		catalog: ProductResponse[],
		apiScanFallback?: ApiScanFn,
	): Promise<void> {
		this.currentCatalog = catalog;
		const resolution = await resolveBarcodeScan(
			barcode,
			catalog,
			apiScanFallback,
		);
		if (!resolution) return;

		if (resolution.type === 'prompt_weight') {
			this.openWeightModal(resolution.product, {
				initialWeightGrams: resolution.initialWeightGrams,
			});
			await playBeep()?.catch?.(() => {});
			return;
		}

		if (resolution.type === 'add_to_cart') {
			cart.addItem(resolution.product, resolution.options);
			await playBeep()?.catch?.(() => {});
			this.showNotification(`+ ${resolution.product.name}`, 'success');
			return;
		}

		if (resolution.type === 'error') {
			await playError()?.catch?.(() => {});
			this.showNotification(resolution.message, 'error');
		}
	}

	handleKeydown(e: KeyboardEvent, catalog: ProductResponse[]): void {
		this.currentCatalog = catalog;
		this.hardwareScanner.handleKeydown(e);
	}

	handleProductSelect(product: ProductResponse): void {
		if (product.product_type === 'bulk') {
			this.openWeightModal(product, {
				initialWeightGrams: product.bulk_reference_grams || 100,
			});
		} else {
			cart.addItem(product);
			playBeep()?.catch?.(() => {});
			this.showNotification(`+ ${product.name}`, 'success');
		}
	}

	handleEditItemWeight(item: CartItem): void {
		this.openWeightModal(item.product, {
			itemId: item.id,
			initialWeightGrams: item.weightGrams || 100,
		});
	}

	handleWeightConfirm(weightGrams: number): void {
		if (this.activeWeightItemId) {
			cart.updateWeight(this.activeWeightItemId, weightGrams);
			playBeep()?.catch?.(() => {});
			this.showNotification(
				`Peso actualizado a ${formatWeight(weightGrams)}`,
				'success',
			);
		} else if (this.activeWeightProduct) {
			cart.addItem(this.activeWeightProduct, { weightGrams });
			playBeep()?.catch?.(() => {});
			this.showNotification(
				`+ ${this.activeWeightProduct.name} (${formatWeight(weightGrams)})`,
				'success',
			);
		}

		this.closeWeightModal();
	}

	handleClearCart(): void {
		cart.clearCart();
		this.isClearConfirmOpen = false;
		this.showNotification('Carrito vaciado', 'info');
	}

	handleCheckoutSuccess(): void {
		cart.clearCart();
	}
}
