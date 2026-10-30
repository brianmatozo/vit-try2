import type { FinancialClosureResponse } from '@vitalcer/api';

export type NotificationType = 'success' | 'error' | 'info';

export interface ClosureNotification {
	type: NotificationType;
	message: string;
}

export class ClosureState {
	isOpenModalOpen = $state(false);
	isMovementModalOpen = $state(false);
	isArqueoModalOpen = $state(false);
	isReceiptModalOpen = $state(false);

	selectedReceiptClosure = $state<FinancialClosureResponse | null>(null);
	notification = $state<ClosureNotification | null>(null);

	openModal() {
		this.isOpenModalOpen = true;
	}

	closeOpenModal() {
		this.isOpenModalOpen = false;
	}

	openMovementModal() {
		this.isMovementModalOpen = true;
	}

	closeMovementModal() {
		this.isMovementModalOpen = false;
	}

	openArqueoModal() {
		this.isArqueoModalOpen = true;
	}

	closeArqueoModal() {
		this.isArqueoModalOpen = false;
	}

	openReceipt(closure: FinancialClosureResponse) {
		this.selectedReceiptClosure = closure;
		this.isReceiptModalOpen = true;
	}

	closeReceipt() {
		this.isReceiptModalOpen = false;
		this.selectedReceiptClosure = null;
	}

	showNotification(type: NotificationType, message: string) {
		this.notification = { type, message };
		setTimeout(() => {
			if (this.notification?.message === message) {
				this.notification = null;
			}
		}, 4500);
	}

	clearNotification() {
		this.notification = null;
	}
}
