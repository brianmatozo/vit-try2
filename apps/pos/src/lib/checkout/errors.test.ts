import { extractApiError, getApiErrorMessage } from '@vitalcer/api';
import { describe, expect, it } from 'vitest';

describe('extractApiError & getApiErrorMessage', () => {
	it('extracts detail and code from Vitalcer domain exceptions', () => {
		const errorPayload = {
			detail:
				"Physical stock depleted for 'Almendras': requested 5, available 2",
			code: 'INSUFFICIENT_STOCK',
		};

		const result = extractApiError(errorPayload);
		expect(result.message).toBe(
			"Physical stock depleted for 'Almendras': requested 5, available 2",
		);
		expect(result.code).toBe('INSUFFICIENT_STOCK');
		expect(getApiErrorMessage(errorPayload)).toBe(
			"Physical stock depleted for 'Almendras': requested 5, available 2",
		);
	});

	it('handles legacy or standard HTTPException with detail string and no code', () => {
		const errorPayload = {
			detail: 'Product with ID 99 not found',
		};

		const result = extractApiError(errorPayload);
		expect(result.message).toBe('Product with ID 99 not found');
		expect(result.code).toBeUndefined();
	});

	it('handles FastAPI 422 validation error arrays cleanly without crashing', () => {
		const validationError = {
			detail: [
				{
					loc: ['body', 'items', 0, 'quantity'],
					msg: 'Input should be greater than 0',
					type: 'greater_than',
				},
				{
					loc: ['body', 'ticket_reference_id'],
					msg: 'Field required',
					type: 'missing',
				},
			],
		};

		const result = extractApiError(validationError);
		expect(result.code).toBe('VALIDATION_ERROR');
		expect(result.message).toBe(
			'items.0.quantity: Input should be greater than 0; ticket_reference_id: Field required',
		);
	});

	it('handles standard JavaScript Error instances', () => {
		const jsError = new Error('Network connection dropped');
		const result = extractApiError(jsError);
		expect(result.message).toBe('Network connection dropped');
	});

	it('handles raw strings', () => {
		const result = extractApiError('Direct error string');
		expect(result.message).toBe('Direct error string');
	});

	it('falls back gracefully on null, undefined, or empty objects', () => {
		expect(extractApiError(null, 'Fallback msg').message).toBe('Fallback msg');
		expect(extractApiError(undefined, 'Fallback msg').message).toBe(
			'Fallback msg',
		);
		expect(extractApiError({}, 'Fallback msg').message).toBe('Fallback msg');
	});
});
