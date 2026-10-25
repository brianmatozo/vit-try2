<script lang="ts">
import {
	AlertCircle,
	Flashlight,
	FlashlightOff,
	RefreshCw,
} from 'lucide-svelte';
import { untrack } from 'svelte';
import { CameraScannerController } from './camera-scanner.svelte';

interface Props {
	onscan: (barcode: string) => void;
	active?: boolean;
}

let { onscan, active = true }: Props = $props();

const scanner = new CameraScannerController({ onscan: (code) => onscan(code) });

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

<div class="relative w-full overflow-hidden rounded-2xl bg-black shadow-lg border border-neutral-800">
	<video
		bind:this={scanner.videoElement}
		playsinline
		muted
		autoplay
		class="w-full h-48 sm:h-56 object-cover"
	></video>

	{#if scanner.isScanning && !scanner.cameraError}
		<div class="absolute inset-0 pointer-events-none flex items-center justify-center p-4">
			{#if scanner.scanSuccessFlash}
				<div class="absolute inset-0 bg-emerald-500/30 transition-opacity duration-300"></div>
			{/if}

			<!-- Viewfinder reticle with corner brackets -->
			<div class="relative w-4/5 max-w-[280px] h-28 border-2 border-dashed border-emerald-400/70 rounded-xl flex items-center justify-center">
				<div class="absolute -top-1 -left-1 w-4 h-4 border-t-2 border-l-2 border-emerald-400"></div>
				<div class="absolute -top-1 -right-1 w-4 h-4 border-t-2 border-r-2 border-emerald-400"></div>
				<div class="absolute -bottom-1 -left-1 w-4 h-4 border-b-2 border-l-2 border-emerald-400"></div>
				<div class="absolute -bottom-1 -right-1 w-4 h-4 border-b-2 border-r-2 border-emerald-400"></div>
				<div class="w-full h-0.5 bg-gradient-to-r from-transparent via-emerald-400 to-transparent shadow-[0_0_8px_rgba(52,211,153,0.8)] animate-pulse"></div>
			</div>
		</div>

		<!-- Scanner controls overlay -->
		<div class="absolute bottom-2 inset-x-2 flex items-center justify-between pointer-events-auto">
			<div class="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/60 backdrop-blur-md text-xs font-medium text-emerald-400 border border-emerald-500/20">
				<span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
				<span>Apuntar al código</span>
			</div>

			<div class="flex items-center gap-2">
				{#if scanner.hasTorch}
					<button
						type="button"
						onclick={() => scanner.toggleTorch()}
						class="p-2 rounded-full bg-black/60 backdrop-blur-md text-white hover:bg-neutral-800 transition active:scale-95 border border-white/10"
						aria-label={scanner.isTorchOn ? 'Apagar linterna' : 'Encender linterna'}
					>
						{#if scanner.isTorchOn}
							<Flashlight class="w-4 h-4 text-amber-400 fill-amber-400" />
						{:else}
							<FlashlightOff class="w-4 h-4 text-neutral-400" />
						{/if}
					</button>
				{/if}

				<button
					type="button"
					onclick={() => scanner.switchCamera()}
					class="p-2 rounded-full bg-black/60 backdrop-blur-md text-white hover:bg-neutral-800 transition active:scale-95 border border-white/10"
					aria-label="Cambiar cámara"
				>
					<RefreshCw class="w-4 h-4 text-neutral-300" />
				</button>
			</div>
		</div>
	{/if}

	{#if scanner.cameraError}
		<div class="absolute inset-0 bg-neutral-900/95 flex flex-col items-center justify-center p-6 text-center text-white">
			<AlertCircle class="w-10 h-10 text-rose-400 mb-2" />
			<p class="text-sm font-medium text-neutral-200 mb-3">{scanner.cameraError}</p>
			<button
				type="button"
				onclick={() => scanner.startCamera()}
				class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white text-xs font-semibold rounded-xl shadow-md transition"
			>
				Reintentar Cámara
			</button>
		</div>
	{/if}
</div>
