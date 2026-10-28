<script lang="ts">
import { Button, Card } from '@vitalcer/ui';
import {
	ChevronLeft,
	ChevronRight,
	FileText,
	RotateCcw,
	ZoomIn,
	ZoomOut,
} from 'lucide-svelte';
import type { RemitoDetailState } from '../remito-detail-state.svelte';

interface Props {
	detailState: RemitoDetailState;
}

let { detailState }: Props = $props();

const activeImage = $derived(
	detailState.imageUrls[detailState.activePageIndex] || null,
);
</script>

<Card class="lightbox-card border border-gray-200">
	<!-- Header / Controls Bar -->
	<div class="p-2 sm:p-3 bg-gray-950/80 border-b border-gray-800 flex items-center justify-between gap-2 shrink-0">
		<div class="flex items-center gap-1.5 text-xs font-semibold">
			<FileText class="w-4 h-4 text-emerald-400" />
			<span>Comprobante Físico</span>
			{#if detailState.imageUrls.length > 1}
				<span class="text-2xs px-2 py-0.5 rounded-full bg-gray-800 text-gray-300">
					Pág. {detailState.activePageIndex + 1} de {detailState.imageUrls.length}
				</span>
			{/if}
		</div>

		<!-- Zoom & Page Buttons -->
		<div class="flex items-center gap-1">
			{#if detailState.imageUrls.length > 1}
				<Button
					variant="outline"
					size="sm"
					class="h-7 w-7 p-0 bg-gray-800 border-gray-700 text-gray-300 hover:text-white"
					disabled={detailState.activePageIndex === 0}
					onclick={() => detailState.setPage(detailState.activePageIndex - 1)}
					title="Página anterior"
				>
					<ChevronLeft class="w-4 h-4" />
				</Button>
				<Button
					variant="outline"
					size="sm"
					class="h-7 w-7 p-0 bg-gray-800 border-gray-700 text-gray-300 hover:text-white"
					disabled={detailState.activePageIndex >= detailState.imageUrls.length - 1}
					onclick={() => detailState.setPage(detailState.activePageIndex + 1)}
					title="Página siguiente"
				>
					<ChevronRight class="w-4 h-4" />
				</Button>
			{/if}

			<div class="h-4 w-px bg-gray-700 mx-1"></div>

			<Button
				variant="outline"
				size="sm"
				class="h-7 w-7 p-0 bg-gray-800 border-gray-700 text-gray-300 hover:text-white"
				onclick={() => detailState.zoomOut()}
				title="Alejar"
			>
				<ZoomOut class="w-3.5 h-3.5" />
			</Button>

			<span class="text-2xs font-mono text-gray-400 w-9 text-center">
				{Math.round(detailState.zoomLevel * 100)}%
			</span>

			<Button
				variant="outline"
				size="sm"
				class="h-7 w-7 p-0 bg-gray-800 border-gray-700 text-gray-300 hover:text-white"
				onclick={() => detailState.zoomIn()}
				title="Acercar"
			>
				<ZoomIn class="w-3.5 h-3.5" />
			</Button>

			<Button
				variant="outline"
				size="sm"
				class="h-7 w-7 p-0 bg-gray-800 border-gray-700 text-gray-300 hover:text-white"
				onclick={() => detailState.resetZoom()}
				title="Restablecer zoom"
			>
				<RotateCcw class="w-3.5 h-3.5" />
			</Button>
		</div>
	</div>

	<!-- Image Canvas Viewport -->
	<div class="flex-1 overflow-auto p-4 flex items-center justify-center bg-gray-900/90 relative select-none">
		{#if activeImage}
			<div
				class="transition-transform duration-100 ease-out origin-center"
				style="transform: scale({detailState.zoomLevel});"
			>
				<img
					src={activeImage}
					alt="Comprobante remito página {detailState.activePageIndex + 1}"
					class="lightbox-img shadow-2xl rounded"
					draggable="false"
				/>
			</div>
		{:else}
			<div class="text-center p-8 text-gray-500">
				<FileText class="w-12 h-12 mx-auto mb-2 text-gray-600" />
				<div class="text-sm font-semibold text-gray-400">Sin foto adjunta</div>
				<p class="text-2xs text-gray-600 mt-1 max-w-xs">
					Este remito fue generado sin fotos o cargado mediante simulación.
				</p>
			</div>
		{/if}
	</div>
</Card>

<style>
	:global(.lightbox-card) {
		display: flex;
		flex-direction: column;
		height: 100%;
		overflow: hidden;
		background-color: var(--color-gray-900, #111827);
		color: #ffffff;
		min-height: 26rem;
	}
	@media (min-width: 640px) {
		:global(.lightbox-card) {
			min-height: 35rem;
		}
	}
	.lightbox-img {
		max-width: 100%;
		max-height: 72dvh;
		object-fit: contain;
	}
</style>
