import { extractApiError, recordPosBatchSale } from '@vitalcer/api';
import { playError, playSuccess } from '$lib/audio/sound';
import type { CartItem } from '$lib/cart/cart.svelte';

export type PaymentMethod = 'cash' | 'card' | 'qr';

export interface CompletedTicket {
	ticketId: string;
	total: number;
	method: PaymentMethod;
	cashTendered?: number;
	change?: number;
	itemCount: number;
	timestamp: string;
}

export type BatchSaleApiFn = typeof recordPosBatchSale;

export class CheckoutState {
	paymentMethod = $state<PaymentMethod>('cash');
	cashTendered = $state<number>(0);
	isProcessing = $state<boolean>(false);
	errorMessage = $state<string | null>(null);
	errorCode = $state<string | null>(null);
	isRegisterClosed = $state<boolean>(false);
	completedTicket = $state<CompletedTicket | null>(null);

	initCash(total: number): void {
		this.cashTendered = total;
	}

	setCashAmount(amount: number): void {
		this.cashTendered = amount;
	}

	addCashAmount(bill: number, total: number): void {
		if (this.cashTendered < total) {
			this.cashTendered = bill;
		} else {
			this.cashTendered += bill;
		}
	}

	getChange(total: number): number {
		return this.cashTendered - total;
	}

	isCashValid(total: number): boolean {
		return this.paymentMethod !== 'cash' || this.cashTendered >= total;
	}

	reset(initialAmount = 0): void {
		this.paymentMethod = 'cash';
		this.cashTendered = initialAmount;
		this.isProcessing = false;
		this.errorMessage = null;
		this.errorCode = null;
		this.isRegisterClosed = false;
		this.completedTicket = null;
	}

	async confirmSale(
		items: CartItem[],
		total: number,
		totalUnits: number,
		onCompleteCallback: () => void,
		apiBatchSale: BatchSaleApiFn = recordPosBatchSale,
	): Promise<boolean> {
		if (items.length === 0) return false;

		if (this.paymentMethod === 'cash' && this.cashTendered < total) {
			this.errorMessage =
				'El monto en efectivo ingresado es menor al total de la venta.';
			await playError()?.catch?.(() => {});
			return false;
		}

		this.isProcessing = true;
		this.errorMessage = null;
		this.errorCode = null;
		this.isRegisterClosed = false;

		const ticketId = `POS-${Date.now().toString().slice(-6)}`;
		const itemsToProcess = [...items];

		try {
			const payloadItems = itemsToProcess.map((item) => ({
				product_id: item.product.id,
				quantity: item.isBulk ? (item.weightGrams ?? 1) : item.quantity,
			}));

			const response = await apiBatchSale({
				body: {
					ticket_reference_id: ticketId,
					items: payloadItems,
					payment_method: this.paymentMethod,
					total_amount: total,
					cash_tendered:
						this.paymentMethod === 'cash' ? this.cashTendered : undefined,
					change_returned:
						this.paymentMethod === 'cash'
							? Math.max(0, this.getChange(total))
							: undefined,
				},
			});

			if (response.error) {
				const { message, code } = extractApiError(
					response.error,
					'Error procesando la venta',
				);
				if (code === 'REGISTER_CLOSED') {
					this.isRegisterClosed = true;
					this.errorCode = 'REGISTER_CLOSED';
				}
				throw new Error(message);
			}

			await playSuccess()?.catch?.(() => {});

			const change = this.getChange(total);
			this.completedTicket = {
				ticketId,
				total,
				method: this.paymentMethod,
				cashTendered:
					this.paymentMethod === 'cash' ? this.cashTendered : undefined,
				change: this.paymentMethod === 'cash' ? Math.max(0, change) : undefined,
				itemCount: totalUnits,
				timestamp: new Date().toLocaleTimeString('es-AR', {
					hour: '2-digit',
					minute: '2-digit',
					second: '2-digit',
				}),
			};

			onCompleteCallback();
			return true;
		} catch (err: unknown) {
			const error = err as Error;
			console.error('POS Sale Error:', error);
			if (
				typeof window !== 'undefined' &&
				typeof navigator !== 'undefined' &&
				navigator.onLine === false
			) {
				this.errorMessage =
					'Sin conexión a internet: no se pudo registrar la venta en la base de datos.';
			} else {
				this.errorMessage =
					error.message || 'Error al registrar el cobro en el sistema.';
			}
			await playError()?.catch?.(() => {});
			return false;
		} finally {
			this.isProcessing = false;
		}
	}
}
