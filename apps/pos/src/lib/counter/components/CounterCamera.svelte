<script lang="ts">
import { ChevronDown, ChevronUp } from 'lucide-svelte';
import CameraScanner from '$lib/camera/CameraScanner.svelte';

interface Props {
	isActive: boolean;
	isCollapsed: boolean;
	onToggleCollapse: () => void;
	onScan: (barcode: string) => void;
}

let { isActive, isCollapsed, onToggleCollapse, onScan }: Props = $props();
</script>

<div class="p-3 bg-neutral-900 border-b border-neutral-800/80 transition-all duration-300">
	<div class="flex items-center justify-between mb-2 px-1">
		<div class="flex items-center gap-2 text-xs font-semibold text-neutral-400">
			<span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
			<span>Lector de Cámara</span>
		</div>
		<button
			type="button"
			onclick={onToggleCollapse}
			class="text-xs font-semibold text-neutral-400 hover:text-neutral-200 flex items-center gap-1 transition"
		>
			<span>{isCollapsed ? 'Expandir' : 'Minimizar'}</span>
			{#if isCollapsed}
				<ChevronDown class="w-3.5 h-3.5" />
			{:else}
				<ChevronUp class="w-3.5 h-3.5" />
			{/if}
		</button>
	</div>

	{#if !isCollapsed}
		<CameraScanner
			active={isActive}
			onscan={onScan}
		/>
	{/if}
</div>
