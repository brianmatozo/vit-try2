import { renderSnippet } from '@tanstack/svelte-table';
import type { ProductResponse } from '@vitalcer/api';
import { formatARS, formatWeight } from '@vitalcer/core';
import type { Snippet } from 'svelte';
import { createAppColumnHelper } from '$lib/table';

export interface CatalogColumnSnippets {
	nameCell: Snippet<[ProductResponse]>;
	typeCell: Snippet<[string | undefined]>;
	statusCell: Snippet<[boolean | undefined]>;
	actionsCell: Snippet<[ProductResponse]>;
}

const columnHelper = createAppColumnHelper<ProductResponse>();

export function createCatalogColumns(snippets: CatalogColumnSnippets) {
	return columnHelper.columns([
		columnHelper.accessor('sku', {
			header: 'PLU / Código',
			cell: (info) => info.getValue(),
			meta: { className: 'hidden md:table-cell' },
		}),
		columnHelper.accessor('plu_code', {
			header: 'PLU',
			cell: (info) => info.getValue() ?? '—',
			meta: { className: 'hidden md:table-cell' },
		}),
		columnHelper.accessor('name', {
			header: 'Nombre del Producto',
			cell: (info) => renderSnippet(snippets.nameCell, info.row.original),
		}),
		columnHelper.accessor('product_type', {
			header: 'Tipo',
			cell: (info) => renderSnippet(snippets.typeCell, info.getValue()),
			meta: { className: 'hidden lg:table-cell' },
		}),
		columnHelper.accessor('unit_price', {
			header: 'Precio',
			cell: (info) => formatARS(info.getValue()),
		}),
		columnHelper.accessor('current_stock', {
			header: 'Stock',
			cell: (info) => {
				const row = info.row.original;
				return row.product_type === 'bulk'
					? formatWeight(info.getValue())
					: `${info.getValue()} u`;
			},
		}),
		columnHelper.accessor('reserved_stock', {
			header: 'Reservado',
			cell: (info) => {
				const row = info.row.original;
				const val = info.getValue();
				if (!val) return '0';
				return row.product_type === 'bulk' ? formatWeight(val) : `${val} u`;
			},
			meta: { className: 'hidden lg:table-cell' },
		}),
		columnHelper.accessor('virtual_stock', {
			header: 'Stock Virtual',
			cell: (info) => {
				const row = info.row.original;
				const val = info.getValue();
				return row.product_type === 'bulk' ? formatWeight(val) : `${val} u`;
			},
			meta: { className: 'hidden sm:table-cell' },
		}),
		columnHelper.accessor('is_active', {
			header: 'Estado',
			cell: (info) => renderSnippet(snippets.statusCell, info.getValue()),
			meta: { className: 'hidden md:table-cell' },
		}),
		columnHelper.display({
			id: 'actions',
			header: 'Acciones',
			cell: (info) => renderSnippet(snippets.actionsCell, info.row.original),
		}),
	]);
}
