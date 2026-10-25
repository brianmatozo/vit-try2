import type { InventoryMovementType } from '@vitalcer/api';
import type { Snippet } from 'svelte';
import { describe, expect, it } from 'vitest';
import { createLedgerColumns, formatLedgerDate } from './columns';

const mockSnippets = {
	productLinkSnippet: (() => {}) as unknown as Snippet<[number]>,
	movementTypeSnippet: (() => {}) as unknown as Snippet<
		[InventoryMovementType]
	>,
	deltaSnippet: (() => {}) as unknown as Snippet<[number]>,
};

describe('createLedgerColumns', () => {
	it('creates 8 columns with expected accessors', () => {
		const columns = createLedgerColumns(mockSnippets);
		expect(columns).toHaveLength(8);

		const accessors = columns.map((col) =>
			'accessorKey' in col ? col.accessorKey : col.id,
		);
		expect(accessors).toEqual([
			'id',
			'created_at',
			'product_id',
			'movement_type',
			'quantity_delta',
			'balance_after',
			'reference_id',
			'notes',
		]);
	});
});

describe('formatLedgerDate', () => {
	it('formats valid ISO dates', () => {
		const formatted = formatLedgerDate('2026-10-25T14:30:00Z');
		expect(formatted).toBeTruthy();
		expect(typeof formatted).toBe('string');
	});

	it('safely returns fallback on invalid dates', () => {
		expect(formatLedgerDate('not-a-date')).toBe('not-a-date');
	});
});
