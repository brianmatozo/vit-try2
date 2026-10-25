<script lang="ts">
import { Camera, CameraOff, Trash2 } from 'lucide-svelte';

interface Props {
	itemsCount: number;
	isCameraActive: boolean;
	hasItems: boolean;
	onToggleCamera: () => void;
	onOpenClearConfirm: () => void;
}

let {
	itemsCount,
	isCameraActive,
	hasItems,
	onToggleCamera,
	onOpenClearConfirm,
}: Props = $props();
</script>

<header class="px-3 py-2 bg-neutral-900/90 backdrop-blur-md border-b border-neutral-800 flex items-center justify-between shrink-0 sticky top-0 z-30">
	<div class="flex items-center gap-2 text-xs font-semibold text-neutral-400">
		{#if hasItems}
			<span class="text-emerald-400 font-bold">{itemsCount} {itemsCount === 1 ? 'ítem' : 'ítems'}</span>
		{:else}
			<span class="text-neutral-500">Mostrador</span>
		{/if}
	</div>

	<div class="flex items-center gap-2">
		<!-- Camera toggle button -->
		<button
			type="button"
			onclick={onToggleCamera}
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
		{#if hasItems}
			<button
				type="button"
				onclick={onOpenClearConfirm}
				class="p-2 rounded-xl bg-neutral-800 hover:bg-rose-950/40 hover:text-rose-400 border border-neutral-700 hover:border-rose-800/40 text-neutral-400 transition"
				aria-label="Vaciar carrito"
			>
				<Trash2 class="w-4 h-4" />
			</button>
		{/if}
	</div>
</header>
