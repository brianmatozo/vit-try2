import type {
	ProductCreate,
	ProductResponse,
	ProductType,
	ProductUpdate,
} from '@vitalcer/api';

export class ProductFormState {
	isOpen = $state(false);
	editingProduct = $state<ProductResponse | null>(null);

	sku = $state('');
	name = $state('');
	productType = $state<ProductType>('discrete');
	unitPrice = $state<number | ''>('');
	bulkReferenceGrams = $state(100);
	pluCode = $state('');
	initialStock = $state(0);
	minSafetyBuffer = $state(0);
	isActive = $state(true);
	syncPedidosya = $state(true);
	syncRappi = $state(true);
	syncVgo = $state(true);
	syncMercadolibre = $state(false);

	formError = $state<string | null>(null);

	isEditing = $derived(this.editingProduct !== null);
	dialogTitle = $derived(
		this.isEditing ? 'Editar Producto' : 'Crear Nuevo Producto',
	);
	dialogDescription = $derived(
		this.isEditing
			? 'Modifica los datos del artículo seleccionado.'
			: 'Registra un nuevo artículo discreto o a granel en el sistema.',
	);

	openCreate(): void {
		this.editingProduct = null;
		this.sku = '';
		this.name = '';
		this.productType = 'discrete';
		this.unitPrice = '';
		this.bulkReferenceGrams = 100;
		this.pluCode = '';
		this.initialStock = 0;
		this.minSafetyBuffer = 0;
		this.isActive = true;
		this.syncPedidosya = true;
		this.syncRappi = true;
		this.syncVgo = true;
		this.syncMercadolibre = false;
		this.formError = null;
		this.isOpen = true;
	}

	openEdit(product: ProductResponse): void {
		this.editingProduct = product;
		this.sku = product.sku;
		this.name = product.name;
		this.productType = product.product_type ?? 'discrete';
		this.unitPrice = product.unit_price;
		this.bulkReferenceGrams = product.bulk_reference_grams ?? 100;
		this.pluCode = product.plu_code ?? '';
		this.initialStock = product.current_stock;
		this.minSafetyBuffer = product.min_safety_buffer ?? 0;
		this.isActive = product.is_active ?? true;
		this.syncPedidosya = product.sync_pedidosya ?? true;
		this.syncRappi = product.sync_rappi ?? true;
		this.syncVgo = product.sync_vgo ?? true;
		this.syncMercadolibre = product.sync_mercadolibre ?? false;
		this.formError = null;
		this.isOpen = true;
	}

	close(): void {
		this.isOpen = false;
		this.formError = null;
	}

	validate(): boolean {
		this.formError = null;

		if (
			!this.sku.trim() ||
			!this.name.trim() ||
			this.unitPrice === '' ||
			Number(this.unitPrice) <= 0
		) {
			this.formError = 'Completa PLU, nombre y precio unitario mayor a cero.';
			return false;
		}

		if (
			this.productType === 'bulk' &&
			this.pluCode.trim() &&
			!/^\d{4}$/.test(this.pluCode.trim())
		) {
			this.formError =
				'El código PLU para balanza debe ser numérico de 4 dígitos (ej: 0142).';
			return false;
		}

		return true;
	}

	buildCreatePayload(): ProductCreate {
		return {
			sku: this.sku.trim(),
			name: this.name.trim(),
			product_type: this.productType,
			unit_price: Math.round(Number(this.unitPrice)),
			bulk_reference_grams:
				this.productType === 'bulk' ? Number(this.bulkReferenceGrams) : 100,
			plu_code:
				this.productType === 'bulk' && this.pluCode.trim()
					? this.pluCode.trim()
					: null,
			current_stock: Number(this.initialStock),
			min_safety_buffer: Number(this.minSafetyBuffer),
			is_active: this.isActive,
			sync_pedidosya: this.syncPedidosya,
			sync_rappi: this.syncRappi,
			sync_vgo: this.syncVgo,
			sync_mercadolibre: this.syncMercadolibre,
		};
	}

	buildUpdatePayload(): ProductUpdate {
		return {
			sku: this.sku.trim(),
			name: this.name.trim(),
			product_type: this.productType,
			unit_price: Math.round(Number(this.unitPrice)),
			bulk_reference_grams:
				this.productType === 'bulk'
					? Number(this.bulkReferenceGrams)
					: undefined,
			plu_code:
				this.productType === 'bulk' && this.pluCode.trim()
					? this.pluCode.trim()
					: null,
			min_safety_buffer: Number(this.minSafetyBuffer),
			is_active: this.isActive,
			sync_pedidosya: this.syncPedidosya,
			sync_rappi: this.syncRappi,
			sync_vgo: this.syncVgo,
			sync_mercadolibre: this.syncMercadolibre,
		};
	}
}
