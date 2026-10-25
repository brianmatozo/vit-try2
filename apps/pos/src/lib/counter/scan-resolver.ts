import {
	type ProductResponse,
	type ScanBarcodeResponse,
	scanBarcode,
} from '@vitalcer/api';
import { calculateWeightFromPrice, parseBarcode } from '@vitalcer/core';

export type ScanResolution =
	| {
			type: 'add_to_cart';
			product: ProductResponse;
			options: {
				weightGrams?: number;
				lineTotal?: number;
				rawBarcode?: string;
			};
	  }
	| {
			type: 'prompt_weight';
			product: ProductResponse;
			initialWeightGrams: number;
	  }
	| {
			type: 'error';
			message: string;
	  };

export type ApiScanFn = (
	cleanBarcode: string,
) => Promise<{ data?: ScanBarcodeResponse; error?: unknown }>;

const defaultApiScan: ApiScanFn = async (cleanBarcode: string) => {
	const res = await scanBarcode({
		path: { barcode: cleanBarcode },
	});
	return { data: res.data, error: res.error };
};

export async function resolveBarcodeScan(
	barcode: string,
	catalog: ProductResponse[],
	apiScanFallback: ApiScanFn = defaultApiScan,
): Promise<ScanResolution | null> {
	const clean = barcode.trim();
	if (!clean) return null;

	// 1. Instant client lookup from preloaded in-memory catalog (0ms, offline-tolerant)
	const parsed = parseBarcode(clean);
	let prod: ProductResponse | undefined;

	if (catalog.length > 0) {
		if (parsed.isEmbeddedWeight) {
			prod = catalog.find(
				(p) =>
					p.plu_code &&
					p.plu_code.toLowerCase() === parsed.skuOrPlu.toLowerCase(),
			);
		} else {
			prod = catalog.find(
				(p) =>
					p.sku.toLowerCase() === clean.toLowerCase() ||
					(p.plu_code && p.plu_code.toLowerCase() === clean.toLowerCase()),
			);
		}
	}

	if (prod) {
		const isScaleItem =
			parsed.isEmbeddedScale ||
			parsed.isEmbeddedPrice ||
			parsed.isEmbeddedWeight;

		if (prod.product_type === 'bulk' && !isScaleItem) {
			return {
				type: 'prompt_weight',
				product: prod,
				initialWeightGrams: prod.bulk_reference_grams || 100,
			};
		}

		let weightGrams = parsed.weightGrams;
		let lineTotal: number | undefined;

		if (parsed.isEmbeddedPrice && parsed.embeddedPriceWholeArs !== undefined) {
			lineTotal = parsed.embeddedPriceWholeArs;
			const refGrams =
				prod.bulk_reference_grams && prod.bulk_reference_grams > 0
					? prod.bulk_reference_grams
					: 100;
			weightGrams = calculateWeightFromPrice(
				prod.unit_price,
				refGrams,
				lineTotal,
			);
		}

		return {
			type: 'add_to_cart',
			product: prod,
			options: {
				weightGrams,
				lineTotal,
				rawBarcode: parsed.rawBarcode,
			},
		};
	}

	// 2. Fallback to server endpoint if not found in client cache
	try {
		const res = await apiScanFallback(clean);

		if (res.data) {
			const scanResult = res.data;
			const serverProd = scanResult.product;

			if (
				serverProd.product_type === 'bulk' &&
				!scanResult.is_embedded_weight
			) {
				return {
					type: 'prompt_weight',
					product: serverProd,
					initialWeightGrams: serverProd.bulk_reference_grams || 100,
				};
			}

			return {
				type: 'add_to_cart',
				product: serverProd,
				options: {
					weightGrams: scanResult.weight_grams ?? undefined,
					lineTotal: scanResult.line_total,
					rawBarcode: scanResult.raw_barcode,
				},
			};
		}

		if (res.error) {
			const errPayload = res.error as Record<string, unknown> | undefined;
			const msg =
				typeof errPayload?.detail === 'string'
					? errPayload.detail
					: `Código no encontrado: ${clean}`;
			return { type: 'error', message: msg };
		}
	} catch (err: unknown) {
		console.error('Scan error:', err);
		return { type: 'error', message: `Código no encontrado: ${clean}` };
	}

	return { type: 'error', message: `Código no encontrado: ${clean}` };
}
