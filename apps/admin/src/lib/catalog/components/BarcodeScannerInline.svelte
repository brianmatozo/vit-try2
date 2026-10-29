<script lang="ts">
import {
	AlertCircle,
	Flashlight,
	FlashlightOff,
	RefreshCw,
	X,
} from 'lucide-svelte';
import { untrack } from 'svelte';
import { BarcodeScannerController } from '../barcode-scanner.svelte';

interface Props {
	onscan: (barcode: string) => void;
	onclose: () => void;
	active?: boolean;
}

let { onscan, onclose, active = true }: Props = $props();

const scanner = new BarcodeScannerController({
	onscan: (code) => onscan(code),
	singleShot: true,
});

$effect(() => {
	scanner.onscan = onscan;
});

$effect(() => {
	const shouldBeActive = active;
	untrack(() => {
		if (shouldBeActive) {
			scanner.startCamera();
		} else {
			scanner.stopCamera();
		}
	});

	return () => {
		untrack(() => {
			scanner.stopCamera();
		});
	};
});
</script>

<div class="relative w-full overflow-hidden rounded-xl bg-neutral-950 border border-neutral-800 shadow-md">
	<video
		bind:this={scanner.videoElement}
		playsinline
		muted
		autoplay
		class="w-full h-44 sm:h-52 object-cover"
	></video>

	{#if scanner.isScanning && !scanner.cameraError}
		<div class="absolute inset-0 pointer-events-none flex items-center justify-center p-3">
			{#if scanner.scanSuccessFlash}
				<div class="absolute inset-0 bg-emerald-500/30 transition-opacity duration-300"></div>
			{/if}

			<!-- Viewfinder reticle -->
			<div class="relative w-3/4 max-w-xs h-24 border-2 border-dashed border-emerald-400/70 rounded-lg flex items-center justify-center">
				<div class="absolute -top-1 -left-1 w-3 h-3 border-t-2 border-l-2 border-emerald-400"></div>
				<div class="absolute -top-1 -right-1 w-3 h-3 border-t-2 border-r-2 border-emerald-400"></div>
				<div class="absolute -bottom-1 -left-1 w-3 h-3 border-b-2 border-l-2 border-emerald-400"></div>
				<div class="absolute -bottom-1 -right-1 w-3 h-3 border-b-2 border-r-2 border-emerald-400"></div>
				<div class="w-full h-0.5 bg-gradient-to-r from-transparent via-emerald-400 to-transparent shadow-sm animate-pulse"></div>
			</div>
		</div>

		<!-- Scanner controls overlay -->
		<div class="absolute top-2 right-2 flex items-center gap-1.5 pointer-events-auto">
			<button
				type="button"
				onclick={onclose}
				class="p-1.5 rounded-full bg-black/60 backdrop-blur-md text-white hover:bg-neutral-800 transition active:scale-95 border border-white/10"
				aria-label="Cerrar escáner"
			>
				<X class="w-3.5 h-3.5" />
			</button>
		</div>

		<div class="absolute bottom-2 inset-x-2 flex items-center justify-between pointer-events-auto">
			<div class="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-2xs font-medium text-emerald-400 border border-emerald-500/20">
				<span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
				<span>Alineá el código</span>
			</div>

			<div class="flex items-center gap-1.5">
				{#if scanner.hasTorch}
					<button
						type="button"
						onclick={() => scanner.toggleTorch()}
						class="p-1.5 rounded-full bg-black/60 backdrop-blur-md text-white hover:bg-neutral-800 transition active:scale-95 border border-white/10"
						aria-label={scanner.isTorchOn ? 'Apagar linterna' : 'Encender linterna'}
					>
						{#if scanner.isTorchOn}
							<Flashlight class="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
						{:else}
							<FlashlightOff class="w-3.5 h-3.5 text-neutral-400" />
						{/if}
					</button>
				{/if}

				<button
					type="button"
					onclick={() => scanner.switchCamera()}
					class="p-1.5 rounded-full bg-black/60 backdrop-blur-md text-white hover:bg-neutral-800 transition active:scale-95 border border-white/10"
					aria-label="Cambiar cámara"
				>
					<RefreshCw class="w-3.5 h-3.5 text-neutral-300" />
				</button>
			</div>
		</div>
	{/if}

	{#if scanner.cameraError}
		<div class="absolute inset-0 bg-neutral-900/95 flex flex-col items-center justify-center p-4 text-center text-white">
			<AlertCircle class="w-8 h-8 text-rose-400 mb-1.5" />
			<p class="text-xs font-medium text-neutral-200 mb-2 max-w-xs">{scanner.cameraError}</p>
			<div class="flex items-center gap-2">
				<button
					type="button"
					onclick={() => scanner.startCamera()}
					class="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white text-xs font-semibold rounded-lg shadow-sm transition"
				>
					Reintentar
				</button>
				<button
					type="button"
					onclick={onclose}
					class="px-3 py-1 bg-neutral-700 hover:bg-neutral-600 active:scale-95 text-neutral-200 text-xs font-medium rounded-lg transition"
				>
					Cerrar
				</button>
			</div>
		</div>
	{/if}
</div>
