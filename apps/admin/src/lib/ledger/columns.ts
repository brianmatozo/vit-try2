import { renderSnippet } from '@tanstack/svelte-table';
import type {
	InventoryLedgerResponse,
	InventoryMovementType,
} from '@vitalcer/api';
import type { Snippet } from 'svelte';
import { createAppColumnHelper } from '$lib/table';

export interface LedgerColumnSnippets {
	productLinkSnippet: Snippet<[number]>;
	movementTypeSnippet: Snippet<[InventoryMovementType]>;
	deltaSnippet: Snippet<[number]>;
}

export function formatLedgerDate(isoString: string): string {
	const d = new Date(isoString);
	return Number.isNaN(d.getTime())
		? isoString
		: d.toLocaleString('es-AR', {
				dateStyle: 'short',
				timeStyle: 'short',
			});
}

const columnHelper = createAppColumnHelper<InventoryLedgerResponse>();

export function createLedgerColumns(snippets: LedgerColumnSnippets) {
	return columnHelper.columns([
		columnHelper.accessor('id', {
			header: 'ID',
			cell: (info) => `#${info.getValue()}`,
			meta: { className: 'hidden sm:table-cell' },
		}),
		columnHelper.accessor('created_at', {
			header: 'Fecha / Hora',
			cell: (info) => formatLedgerDate(info.getValue()),
		}),
		columnHelper.accessor('product_id', {
			header: 'Art.',
			cell: (info) =>
				renderSnippet(snippets.productLinkSnippet, info.getValue()),
		}),
		columnHelper.accessor('movement_type', {
			header: 'Tipo',
			cell: (info) =>
				renderSnippet(snippets.movementTypeSnippet, info.getValue()),
		}),
		columnHelper.accessor('quantity_delta', {
			header: 'Variación (Δ)',
			cell: (info) => renderSnippet(snippets.deltaSnippet, info.getValue()),
		}),
		columnHelper.accessor('balance_after', {
			header: 'Saldo',
			cell: (info) => `${info.getValue()}`,
		}),
		columnHelper.accessor('reference_id', {
			header: 'Referencia',
			cell: (info) => info.getValue() || '—',
			meta: { className: 'hidden md:table-cell' },
		}),
		columnHelper.accessor('notes', {
			header: 'Observaciones',
			cell: (info) => info.getValue() || '—',
			meta: { className: 'hidden lg:table-cell' },
		}),
	]);
}
