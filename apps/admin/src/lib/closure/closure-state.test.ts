import type { FinancialClosureResponse } from '@vitalcer/api';
import { describe, expect, it } from 'vitest';
import { ClosureState } from './closure-state.svelte.js';

describe('ClosureState', () => {
	it('controls modal open/close states', () => {
		const state = new ClosureState();
		expect(state.isOpenModalOpen).toBe(false);

		state.openModal();
		expect(state.isOpenModalOpen).toBe(true);
		state.closeOpenModal();
		expect(state.isOpenModalOpen).toBe(false);

		state.openMovementModal();
		expect(state.isMovementModalOpen).toBe(true);
		state.closeMovementModal();
		expect(state.isMovementModalOpen).toBe(false);

		state.openArqueoModal();
		expect(state.isArqueoModalOpen).toBe(true);
		state.closeArqueoModal();
		expect(state.isArqueoModalOpen).toBe(false);
	});

	it('manages receipt modal state with payload', () => {
		const state = new ClosureState();
		const mockClosure = {
			id: 10,
			status: 'closed',
			opened_at: '2026-10-30T09:00:00Z',
			initial_cash: 20000,
			total_sales_amount: 50000,
		} as unknown as FinancialClosureResponse;

		state.openReceipt(mockClosure);
		expect(state.isReceiptModalOpen).toBe(true);
		expect(state.selectedReceiptClosure?.id).toBe(10);

		state.closeReceipt();
		expect(state.isReceiptModalOpen).toBe(false);
		expect(state.selectedReceiptClosure).toBeNull();
	});

	it('manages notifications', () => {
		const state = new ClosureState();
		expect(state.notification).toBeNull();

		state.showNotification('success', 'Caja abierta con éxito');
		expect(state.notification?.type).toBe('success');
		expect(state.notification?.message).toBe('Caja abierta con éxito');

		state.clearNotification();
		expect(state.notification).toBeNull();
	});
});
