<script lang="ts">
import { Camera, Search, ShoppingBag } from 'lucide-svelte';

interface Props {
	isCameraActive: boolean;
	onOpenSearch: () => void;
	onActivateCamera: () => void;
}

let { isCameraActive, onOpenSearch, onActivateCamera }: Props = $props();
</script>

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
			onclick={onOpenSearch}
			class="px-4 py-2.5 bg-neutral-800 hover:bg-neutral-700 active:scale-95 text-xs font-bold text-neutral-200 rounded-xl transition border border-neutral-700 flex items-center gap-2 cursor-pointer"
		>
			<Search class="w-4 h-4 text-emerald-400" />
			<span>Buscar Producto</span>
		</button>

		{#if !isCameraActive}
			<button
				type="button"
				onclick={onActivateCamera}
				class="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-xs font-bold text-white rounded-xl transition shadow-md flex items-center gap-2 cursor-pointer"
			>
				<Camera class="w-4 h-4" />
				<span>Activar Cámara</span>
			</button>
		{/if}
	</div>
</div>
