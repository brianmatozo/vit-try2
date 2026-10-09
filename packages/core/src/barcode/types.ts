export interface ParsedBarcode {
	rawBarcode: string;
	isEmbeddedScale: boolean;
	isEmbeddedPrice: boolean;
	isEmbeddedWeight: boolean;
	skuOrPlu: string;
	embeddedPriceWholeArs?: number;
	weightGrams?: number;
}
