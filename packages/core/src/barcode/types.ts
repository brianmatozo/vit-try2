export interface ParsedBarcode {
	rawBarcode: string;
	isEmbeddedWeight: boolean;
	skuOrPlu: string;
	weightGrams?: number;
}
