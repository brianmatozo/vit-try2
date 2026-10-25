<script lang="ts">
import { createQuery } from '@tanstack/svelte-query';
import {
	type ProductResponse,
	productReadMultiApiV1ProductsGetOptions,
} from '@vitalcer/api';
import { cart } from '$lib/cart/cart.svelte';
import ManualWeightModal from '$lib/catalog/ManualWeightModal.svelte';
import ProductSearchModal from '$lib/catalog/ProductSearchModal.svelte';
import CheckoutModal from '$lib/checkout/CheckoutModal.svelte';
import CartEmptyState from '$lib/counter/components/CartEmptyState.svelte';
import CartItemList from '$lib/counter/components/CartItemList.svelte';
import ClearCartModal from '$lib/counter/components/ClearCartModal.svelte';
import CounterCamera from '$lib/counter/components/CounterCamera.svelte';
import CounterFooter from '$lib/counter/components/CounterFooter.svelte';
import CounterHeader from '$lib/counter/components/CounterHeader.svelte';
import CounterNotification from '$lib/counter/components/CounterNotification.svelte';
import { CounterState } from '$lib/counter/counter-state.svelte';

const counter = new CounterState();

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
</script>

<svelte:head>
	<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
	<title>Vitalcer POS Móvil</title>
</svelte:head>

<svelte:window onkeydown={(e) => counter.handleKeydown(e, products)} />

<div class="max-w-md mx-auto w-full min-h-dvh flex flex-col bg-neutral-950 text-neutral-100 selection:bg-emerald-500 selection:text-white">
	<CounterHeader
		itemsCount={cart.items.length}
		isCameraActive={counter.isCameraActive}
		hasItems={!cart.isEmpty}
		onToggleCamera={() => counter.toggleCamera()}
		onOpenClearConfirm={() => counter.openClearConfirm()}
	/>

	<CounterNotification notification={counter.notification} />

	{#if counter.isCameraActive}
		<CounterCamera
			isActive={counter.isCameraActive}
			isCollapsed={counter.isCameraCollapsed}
			onToggleCollapse={() => counter.toggleCameraCollapse()}
			onScan={(barcode) => counter.handleScan(barcode, products)}
		/>
	{/if}

	<main class="flex-1 overflow-y-auto p-3 space-y-2.5 pb-32">
		{#if cart.isEmpty}
			<CartEmptyState
				isCameraActive={counter.isCameraActive}
				onOpenSearch={() => counter.openSearch()}
				onActivateCamera={() => counter.activateCamera()}
			/>
		{:else}
			<CartItemList
				items={cart.items}
				totalUnits={cart.totalUnits}
				totalAmount={cart.totalAmount}
				onEditWeight={(item) => counter.handleEditItemWeight(item)}
				onUpdateQuantity={(id, delta) => cart.updateQuantity(id, delta)}
				onRemove={(id) => cart.removeItem(id)}
			/>
		{/if}
	</main>

	<CounterFooter
		isEmpty={cart.isEmpty}
		totalUnits={cart.totalUnits}
		totalAmount={cart.totalAmount}
		onOpenSearch={() => counter.openSearch()}
		onOpenCheckout={() => counter.openCheckout()}
	/>

	<ProductSearchModal
		bind:open={counter.isSearchOpen}
		onselect={(prod) => counter.handleProductSelect(prod)}
		onclose={() => counter.closeSearch()}
	/>

	{#if counter.isWeightModalOpen}
		<ManualWeightModal
			bind:open={counter.isWeightModalOpen}
			product={counter.activeWeightProduct}
			initialWeight={counter.initialWeightGrams}
			onconfirm={(weight) => counter.handleWeightConfirm(weight)}
			oncancel={() => counter.closeWeightModal()}
		/>
	{/if}

	{#if counter.isCheckoutOpen}
		<CheckoutModal
			bind:open={counter.isCheckoutOpen}
			oncomplete={() => counter.handleCheckoutSuccess()}
			oncancel={() => counter.closeCheckout()}
		/>
	{/if}

	<ClearCartModal
		bind:open={counter.isClearConfirmOpen}
		onConfirm={() => counter.handleClearCart()}
		onCancel={() => counter.closeClearConfirm()}
	/>
</div>
