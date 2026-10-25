import type { ProductResponse } from '@vitalcer/api';
import { parseBarcode } from '@vitalcer/core';

export interface CatalogMetricsData {
	total: number;
	bulk: number;
	discrete: number;
	lowStock: number;
}

/**
 * Filters a list of products matching a search term by name, SKU, PLU,
 * or embedded-weight GS1 scale barcodes (20PPPPPWWWWWC).
 */
export function filterProducts(
	products: ProductResponse[],
	searchTerm: string,
): ProductResponse[] {
	const rawTerm = searchTerm.trim();
	const term = rawTerm.toLowerCase();
	if (!term) return products;

	const parsed = parseBarcode(rawTerm);

	return products.filter((product) => {
		if (parsed.isEmbeddedWeight && product.plu_code) {
			if (product.plu_code.toLowerCase() === parsed.skuOrPlu.toLowerCase()) {
				return true;
			}
		}

		return (
			product.name.toLowerCase().includes(term) ||
			product.sku.toLowerCase().includes(term) ||
			Boolean(product.plu_code?.toLowerCase().includes(term))
		);
	});
}

/**
 * Aggregates summary catalog KPIs for active inventory metrics cards.
 */
export function calculateCatalogMetrics(
	products: ProductResponse[],
): CatalogMetricsData {
	let bulk = 0;
	let discrete = 0;
	let lowStock = 0;

	for (const p of products) {
		if (p.product_type === 'bulk') {
			bulk += 1;
		} else if (p.product_type === 'discrete') {
			discrete += 1;
		}

		if (p.current_stock <= 0) {
			lowStock += 1;
		}
	}

	return {
		total: products.length,
		bulk,
		discrete,
		lowStock,
	};
}
