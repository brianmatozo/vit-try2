<script lang="ts">
import { createQuery } from '@tanstack/svelte-query';
import {
	type ProductResponse,
	productReadMultiApiV1ProductsGetOptions,
	scanBarcode,
} from '@vitalcer/api';
import { formatARS, formatWeight, parseBarcode } from '@vitalcer/core';
import {
	AlertCircle,
	Camera,
	CameraOff,
	CheckCircle,
	ChevronDown,
	ChevronUp,
	Minus,
	Package,
	Plus,
	Scale,
	Search,
	ShoppingBag,
	Trash2,
	Volume2,
} from 'lucide-svelte';
import { playBeep, playError } from '$lib/audio/sound';
import CameraScanner from '$lib/camera/CameraScanner.svelte';
import { type CartItem, cart } from '$lib/cart/cart.svelte';
import ManualWeightModal from '$lib/catalog/ManualWeightModal.svelte';
import ProductSearchModal from '$lib/catalog/ProductSearchModal.svelte';
import CheckoutModal from '$lib/checkout/CheckoutModal.svelte';

// Preload product catalog into TanStack Query memory cache for 0ms offline-tolerant scans
const productsQuery = createQuery(() =>
	productReadMultiApiV1ProductsGetOptions({
		query: { limit: 1000 },
	}),
);

const products = $derived<ProductResponse[]>(
	productsQuery.data && 'data' in productsQuery.data
		? (productsQuery.data.data as ProductResponse[])
		: Array.isArray(productsQuery.data)
			? (productsQuery.data as ProductResponse[])
			: [],
);

// Scanner state
let isCameraActive = $state(true);
let isCameraCollapsed = $state(false);

// Modals
let isSearchOpen = $state(false);
let isWeightModalOpen = $state(false);
let isCheckoutOpen = $state(false);
let isClearConfirmOpen = $state(false);

// Bulk item weight editing
let activeWeightProduct = $state<ProductResponse | null>(null);
let activeWeightItemId = $state<string | null>(null);
let initialWeightGrams = $state(100);

// Notification banner
let notification = $state<{
	message: string;
	type: 'success' | 'error' | 'info';
} | null>(null);
let notificationTimer: ReturnType<typeof setTimeout> | null = null;

function showNotification(
	message: string,
	type: 'success' | 'error' | 'info' = 'info',
) {
	if (notificationTimer) clearTimeout(notificationTimer);
	notification = { message, type };
	notificationTimer = setTimeout(() => {
		notification = null;
	}, 2800);
}

// Unified barcode scan handler: fast local cache first, backend fallback second
async function handleBarcodeScan(barcode: string) {
	const clean = barcode.trim();
	if (!clean) return;

	// 1. Try instant client lookup from preloaded in-memory catalog (0ms, offline-tolerant)
	const parsed = parseBarcode(clean);
	let prod: ProductResponse | undefined;

	if (products.length > 0) {
		if (parsed.isEmbeddedWeight) {
			prod = products.find(
				(p) =>
					p.plu_code &&
					p.plu_code.toLowerCase() === parsed.skuOrPlu.toLowerCase(),
			);
		} else {
			prod = products.find(
				(p) =>
					p.sku.toLowerCase() === clean.toLowerCase() ||
					(p.plu_code && p.plu_code.toLowerCase() === clean.toLowerCase()),
			);
		}
	}

	if (prod) {
		if (prod.product_type === 'bulk' && !parsed.isEmbeddedWeight) {
			activeWeightProduct = prod;
			activeWeightItemId = null;
			initialWeightGrams = prod.bulk_reference_grams || 100;
			isWeightModalOpen = true;
			await playBeep();
			return;
		}

		cart.addItem(prod, {
			weightGrams: parsed.weightGrams,
			rawBarcode: parsed.rawBarcode,
		});

		await playBeep();
		showNotification(`+ ${prod.name}`, 'success');
		return;
	}

	// 2. Fallback to server endpoint if not found in client cache
	try {
		const res = await scanBarcode({
			path: { barcode: clean },
		});

		if (res.data) {
			const scanResult = res.data;
			const serverProd = scanResult.product;

			if (
				serverProd.product_type === 'bulk' &&
				!scanResult.is_embedded_weight
			) {
				activeWeightProduct = serverProd;
				activeWeightItemId = null;
				initialWeightGrams = serverProd.bulk_reference_grams || 100;
				isWeightModalOpen = true;
				await playBeep();
				return;
			}

			cart.addItem(serverProd, {
				weightGrams: scanResult.weight_grams ?? undefined,
				rawBarcode: scanResult.raw_barcode,
			});

			await playBeep();
			showNotification(`+ ${serverProd.name}`, 'success');
		} else if (res.error) {
			const errPayload = res.error as Record<string, unknown> | undefined;
			const msg =
				typeof errPayload?.detail === 'string'
					? errPayload.detail
					: `Código no encontrado: ${clean}`;
			await playError();
			showNotification(msg, 'error');
		}
	} catch (err: unknown) {
		const error = err as Error;
		console.error('Scan error:', error);
		await playError();
		showNotification(`Código no encontrado: ${clean}`, 'error');
	}
}

// Global Hardware Barcode Scanner (HID Keyboard) listener
let barcodeBuffer = '';
let lastKeyTime = 0;

function handleGlobalKeydown(e: KeyboardEvent) {
	// If cashier is typing in an input or textarea, let normal typing happen
	const target = e.target as HTMLElement | null;
	if (
		target &&
		(target.tagName === 'INPUT' ||
			target.tagName === 'TEXTAREA' ||
			target.isContentEditable)
	) {
		return;
	}

	const now = Date.now();
	// Scanners fire keystrokes in rapid succession (< 50ms per key)
	if (now - lastKeyTime > 200) {
		barcodeBuffer = '';
	}
	lastKeyTime = now;

	if (e.key === 'Enter') {
		if (barcodeBuffer.trim().length >= 3) {
			e.preventDefault();
			const scannedCode = barcodeBuffer.trim();
			barcodeBuffer = '';
			handleBarcodeScan(scannedCode);
		}
	} else if (e.key.length === 1) {
		barcodeBuffer += e.key;
	}
}

// Product search selection handler
function handleProductSelect(product: ProductResponse) {
	if (product.product_type === 'bulk') {
		activeWeightProduct = product;
		activeWeightItemId = null;
		initialWeightGrams = product.bulk_reference_grams || 100;
		isWeightModalOpen = true;
	} else {
		cart.addItem(product);
		playBeep();
		showNotification(`+ ${product.name}`, 'success');
	}
}

// Weight confirmation handler
function handleWeightConfirm(weightGrams: number) {
	if (activeWeightItemId) {
		// Editing existing cart item
		cart.updateWeight(activeWeightItemId, weightGrams);
		playBeep();
		showNotification(
			`Peso actualizado a ${formatWeight(weightGrams)}`,
			'success',
		);
	} else if (activeWeightProduct) {
		// Adding new item
		cart.addItem(activeWeightProduct, { weightGrams });
		playBeep();
		showNotification(
			`+ ${activeWeightProduct.name} (${formatWeight(weightGrams)})`,
			'success',
		);
	}

	activeWeightProduct = null;
	activeWeightItemId = null;
}

function handleEditItemWeight(item: CartItem) {
	activeWeightProduct = item.product;
	activeWeightItemId = item.id;
	initialWeightGrams = item.weightGrams || 100;
	isWeightModalOpen = true;
}

function handleClearCart() {
	cart.clearCart();
	isClearConfirmOpen = false;
	showNotification('Carrito vaciado', 'info');
}

function handleCheckoutSuccess() {
	cart.clearCart();
}
</script>

<svelte:head>
	<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
	<title>Vitalcer POS Móvil</title>
</svelte:head>

<svelte:window onkeydown={handleGlobalKeydown} />

<div class="max-w-md mx-auto w-full min-h-dvh flex flex-col bg-neutral-950 text-neutral-100 selection:bg-emerald-500 selection:text-white">
	<!-- Top App Header -->
	<header class="px-4 py-3 bg-neutral-900/90 backdrop-blur-md border-b border-neutral-800 flex items-center justify-between shrink-0 sticky top-0 z-30">
		<div class="flex items-center gap-2">
			<div class="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-black text-sm">
				V
			</div>
			<div>
				<h1 class="text-sm font-extrabold tracking-tight text-white flex items-center gap-1.5 leading-none">
					<span>Vitalcer POS</span>
					<span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
				</h1>
				<span class="text-[10px] font-medium text-neutral-400">Caja Mostrador</span>
			</div>
		</div>

		<div class="flex items-center gap-2">
			<!-- Camera toggle button -->
			<button
				type="button"
				onclick={() => (isCameraActive = !isCameraActive)}
				class="p-2 rounded-xl transition border {isCameraActive ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-neutral-800 border-neutral-700 text-neutral-400'}"
				aria-label={isCameraActive ? 'Apagar cámara' : 'Encender cámara'}
			>
				{#if isCameraActive}
					<Camera class="w-4 h-4" />
				{:else}
					<CameraOff class="w-4 h-4" />
				{/if}
			</button>

			<!-- Clear cart button -->
			{#if !cart.isEmpty}
				<button
					type="button"
					onclick={() => (isClearConfirmOpen = true)}
					class="p-2 rounded-xl bg-neutral-800 hover:bg-rose-950/40 hover:text-rose-400 border border-neutral-700 hover:border-rose-800/40 text-neutral-400 transition"
					aria-label="Vaciar carrito"
				>
					<Trash2 class="w-4 h-4" />
				</button>
			{/if}
		</div>
	</header>

	<!-- Notification Toast Banner -->
	{#if notification}
		<div class="fixed top-14 inset-x-4 max-w-sm mx-auto z-50 pointer-events-none transition-all duration-300">
			<div class="px-4 py-2.5 rounded-2xl shadow-xl backdrop-blur-md flex items-center gap-2 text-xs font-bold border {notification.type === 'error' ? 'bg-rose-950/90 text-rose-200 border-rose-700' : notification.type === 'success' ? 'bg-emerald-950/90 text-emerald-200 border-emerald-700' : 'bg-neutral-900/90 text-neutral-200 border-neutral-700'}">
				{#if notification.type === 'error'}
					<AlertCircle class="w-4 h-4 text-rose-400 shrink-0" />
				{:else if notification.type === 'success'}
					<CheckCircle class="w-4 h-4 text-emerald-400 shrink-0" />
				{:else}
					<Volume2 class="w-4 h-4 text-neutral-400 shrink-0" />
				{/if}
				<span class="flex-1 truncate">{notification.message}</span>
			</div>
		</div>
	{/if}

	<!-- Camera Viewfinder Section -->
	{#if isCameraActive}
		<div class="p-3 bg-neutral-900 border-b border-neutral-800/80 transition-all duration-300">
			<div class="flex items-center justify-between mb-2 px-1">
				<div class="flex items-center gap-2 text-xs font-semibold text-neutral-400">
					<span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
					<span>Lector de Cámara</span>
				</div>
				<button
					type="button"
					onclick={() => (isCameraCollapsed = !isCameraCollapsed)}
					class="text-[11px] font-semibold text-neutral-400 hover:text-neutral-200 flex items-center gap-1 transition"
				>
					<span>{isCameraCollapsed ? 'Expandir' : 'Minimizar'}</span>
					{#if isCameraCollapsed}
						<ChevronDown class="w-3.5 h-3.5" />
					{:else}
						<ChevronUp class="w-3.5 h-3.5" />
					{/if}
				</button>
			</div>

			{#if !isCameraCollapsed}
				<CameraScanner
					active={isCameraActive}
					onscan={handleBarcodeScan}
				/>
			{/if}
		</div>
	{/if}

	<!-- Main Body: Cart Items List -->
	<main class="flex-1 overflow-y-auto p-3 space-y-2.5 pb-32">
		{#if cart.isEmpty}
			<!-- Empty Cart State -->
			<div class="py-16 px-4 text-center space-y-4">
				<div class="w-16 h-16 rounded-3xl bg-neutral-900 border border-neutral-800 flex items-center justify-center mx-auto text-neutral-600">
					<ShoppingBag class="w-8 h-8" />
				</div>
				<div>
					<h2 class="text-base font-bold text-neutral-300">Carrito Vacío</h2>
					<p class="text-xs text-neutral-500 max-w-xs mx-auto mt-1">
						Apuntá la cámara a un código de barras o buscá un producto para comenzar el cobro.
					</p>
				</div>

				<div class="flex items-center justify-center gap-2 pt-2">
					<button
						type="button"
						onclick={() => (isSearchOpen = true)}
						class="px-4 py-2.5 bg-neutral-800 hover:bg-neutral-700 active:scale-95 text-xs font-bold text-neutral-200 rounded-xl transition border border-neutral-700 flex items-center gap-2"
					>
						<Search class="w-4 h-4 text-emerald-400" />
						<span>Buscar Producto</span>
					</button>

					{#if !isCameraActive}
						<button
							type="button"
							onclick={() => (isCameraActive = true)}
							class="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-xs font-bold text-white rounded-xl transition shadow-md flex items-center gap-2"
						>
							<Camera class="w-4 h-4" />
							<span>Activar Cámara</span>
						</button>
					{/if}
				</div>
			</div>
		{:else}
			<!-- Items Count & Cart Header -->
			<div class="flex items-center justify-between px-1 text-xs font-semibold text-neutral-400">
				<span>{cart.items.length} {cart.items.length === 1 ? 'ítem' : 'ítems'} ({cart.totalUnits} {cart.totalUnits === 1 ? 'unidad' : 'unidades'})</span>
				<span class="text-emerald-400 font-bold">Subtotal: {formatARS(cart.totalAmount)}</span>
			</div>

			<!-- Cart Item Cards -->
			{#each cart.items as item (item.id)}
				<div class="p-3 bg-neutral-900 rounded-2xl border border-neutral-800 shadow-sm space-y-2.5">
					<div class="flex items-start justify-between gap-2">
						<div class="min-w-0 flex-1">
							<div class="font-bold text-sm text-white truncate">
								{item.product.name}
							</div>
							<div class="flex items-center gap-1.5 mt-0.5 flex-wrap">
								{#if item.isBulk}
									<span class="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
										<Scale class="w-3 h-3 text-amber-400" />
										PLU {item.product.plu_code || '-'}
									</span>
									<span class="text-[11px] text-neutral-400">
										{formatARS(item.unitPrice)} / {item.product.bulk_reference_grams || 100}g
									</span>
								{:else}
									<span class="inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded bg-neutral-800 text-neutral-400 border border-neutral-700">
										<Package class="w-3 h-3 text-neutral-500" />
										{item.product.sku}
									</span>
									<span class="text-[11px] text-neutral-400">
										{formatARS(item.unitPrice)} c/u
									</span>
								{/if}
							</div>
						</div>

						<!-- Line Total & Delete -->
						<div class="text-right shrink-0 flex flex-col items-end">
							<span class="text-base font-black text-emerald-400">
								{formatARS(item.lineTotal)}
							</span>
							<button
								type="button"
								onclick={() => cart.removeItem(item.id)}
								class="p-1 text-neutral-500 hover:text-rose-400 transition -mr-1"
								aria-label="Eliminar ítem"
							>
								<Trash2 class="w-3.5 h-3.5" />
							</button>
						</div>
					</div>

					<!-- Quantity or Weight Stepper Controls -->
					<div class="pt-2 border-t border-neutral-800/80 flex items-center justify-between">
						{#if item.isBulk}
							<!-- Bulk Weight Modifier Button -->
							<button
								type="button"
								onclick={() => handleEditItemWeight(item)}
								class="px-3 py-1.5 bg-neutral-800 hover:bg-neutral-700 active:scale-95 text-xs font-bold text-amber-300 rounded-xl border border-neutral-700 transition flex items-center gap-1.5"
							>
								<Scale class="w-3.5 h-3.5 text-amber-400" />
								<span>{formatWeight(item.weightGrams || 0)}</span>
								<span class="text-[10px] text-neutral-400 font-normal">(Modificar)</span>
							</button>
						{:else}
							<!-- Discrete Unit Stepper -->
							<div class="flex items-center gap-1 bg-neutral-800 rounded-xl p-0.5 border border-neutral-700">
								<button
									type="button"
									onclick={() => cart.updateQuantity(item.id, -1)}
									class="w-8 h-8 rounded-lg bg-neutral-900 text-neutral-300 hover:text-white flex items-center justify-center transition active:scale-90"
									aria-label="Disminuir cantidad"
								>
									<Minus class="w-3.5 h-3.5" />
								</button>

								<span class="w-9 text-center text-sm font-extrabold text-white">
									{item.quantity}
								</span>

								<button
									type="button"
									onclick={() => cart.updateQuantity(item.id, 1)}
									class="w-8 h-8 rounded-lg bg-neutral-900 text-neutral-300 hover:text-white flex items-center justify-center transition active:scale-90"
									aria-label="Aumentar cantidad"
								>
									<Plus class="w-3.5 h-3.5" />
								</button>
							</div>
						{/if}

						<span class="text-[11px] font-medium text-neutral-500">
							Subtotal: {formatARS(item.lineTotal)}
						</span>
					</div>
				</div>
			{/each}
		{/if}
	</main>

	<!-- Fixed Bottom Action Bar -->
	<footer class="fixed bottom-0 inset-x-0 max-w-md mx-auto p-3 bg-neutral-900/95 backdrop-blur-xl border-t border-neutral-800 z-40">
		<div class="flex items-center gap-2">
			<!-- Quick Search Catalog Button -->
			<button
				type="button"
				onclick={() => (isSearchOpen = true)}
				class="h-14 px-4 bg-neutral-800 hover:bg-neutral-700 active:scale-95 text-neutral-200 font-bold rounded-2xl border border-neutral-700 transition flex flex-col items-center justify-center gap-0.5 shrink-0"
			>
				<Search class="w-5 h-5 text-emerald-400" />
				<span class="text-[10px]">Buscar</span>
			</button>

			<!-- Primary Checkout Button -->
			<button
				type="button"
				onclick={() => (isCheckoutOpen = true)}
				disabled={cart.isEmpty}
				class="flex-1 h-14 bg-emerald-600 hover:bg-emerald-500 disabled:bg-neutral-800 disabled:text-neutral-500 text-white font-black rounded-2xl shadow-lg shadow-emerald-600/25 disabled:shadow-none transition active:scale-[0.98] flex items-center justify-between px-5 cursor-pointer disabled:cursor-not-allowed"
			>
				<div class="text-left">
					<div class="text-[10px] uppercase font-bold tracking-wider opacity-80 leading-none">
						{cart.totalUnits} {cart.totalUnits === 1 ? 'artículo' : 'artículos'}
					</div>
					<div class="text-sm font-extrabold leading-tight mt-0.5">
						Cobrar
					</div>
				</div>

				<div class="text-xl font-black tracking-tight text-white">
					{formatARS(cart.totalAmount)}
				</div>
			</button>
		</div>
	</footer>

	<!-- Modals -->
	<ProductSearchModal
		bind:open={isSearchOpen}
		onselect={handleProductSelect}
		onclose={() => (isSearchOpen = false)}
	/>

	<ManualWeightModal
		bind:open={isWeightModalOpen}
		product={activeWeightProduct}
		initialWeight={initialWeightGrams}
		onconfirm={handleWeightConfirm}
		oncancel={() => {
			isWeightModalOpen = false;
			activeWeightProduct = null;
			activeWeightItemId = null;
		}}
	/>

	<CheckoutModal
		bind:open={isCheckoutOpen}
		oncomplete={handleCheckoutSuccess}
		oncancel={() => (isCheckoutOpen = false)}
	/>

	<!-- Clear Cart Confirmation Dialog -->
	{#if isClearConfirmOpen}
		<div class="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
			<div class="bg-neutral-900 border border-neutral-800 rounded-2xl p-5 max-w-xs w-full text-center space-y-4 shadow-2xl">
				<div class="w-12 h-12 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center justify-center mx-auto">
					<Trash2 class="w-6 h-6" />
				</div>
				<div>
					<h3 class="text-base font-bold text-white">¿Vaciar el carrito?</h3>
					<p class="text-xs text-neutral-400 mt-1">Se eliminarán todos los artículos actuales.</p>
				</div>
				<div class="flex items-center gap-2">
					<button
						type="button"
						onclick={() => (isClearConfirmOpen = false)}
						class="flex-1 py-2.5 rounded-xl bg-neutral-800 hover:bg-neutral-700 text-xs font-bold text-neutral-300 transition"
					>
						Cancelar
					</button>
					<button
						type="button"
						onclick={handleClearCart}
						class="flex-1 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-xs font-bold text-white transition shadow-md"
					>
						Vaciar
					</button>
				</div>
			</div>
		</div>
	{/if}
</div>
