<script lang="ts">
import type { ClosureSummaryResponse } from '@vitalcer/api';
import { formatARS } from '@vitalcer/core';
import {
	AlertTriangle,
	ArrowDownRight,
	CheckCircle2,
	Store,
} from 'lucide-svelte';

interface Props {
	summary: ClosureSummaryResponse | null;
	isLoading: boolean;
	onOpenRegister: () => void;
	onOpenCashMovement: () => void;
}

let { summary, isLoading, onOpenRegister, onOpenCashMovement }: Props =
	$props();
</script>

{#if isLoading}
	<div class="px-3 py-1.5 bg-neutral-900 border-b border-neutral-800 text-xs text-neutral-400 flex items-center justify-between">
		<span>Verificando estado de caja...</span>
	</div>
{:else if summary && summary.closure.status === 'open'}
	<div class="px-3 py-1.5 bg-neutral-900 border-b border-neutral-800 text-xs flex items-center justify-between gap-2">
		<div class="flex items-center gap-1.5 min-w-0">
			<span class="inline-block w-2 h-2 rounded-full bg-emerald-400 shrink-0"></span>
			<span class="font-bold text-neutral-200 truncate">Caja Abierta</span>
			<span class="text-neutral-500 font-normal">| En cajón:</span>
			<span class="font-black text-emerald-400">{formatARS(summary.closure.expected_cash)}</span>
		</div>

		<button
			type="button"
			onclick={onOpenCashMovement}
			class="py-1 px-2 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-300 font-semibold text-xs flex items-center gap-1 transition active:scale-95 shrink-0 cursor-pointer"
		>
			<ArrowDownRight class="w-3.5 h-3.5 text-rose-400" />
			<span>+ Gasto</span>
		</button>
	</div>
{:else}
	<div class="px-3 py-2 bg-amber-950/40 border-b border-amber-800/40 text-xs flex items-center justify-between gap-2">
		<div class="flex items-center gap-2 min-w-0">
			<AlertTriangle class="w-4 h-4 text-amber-400 shrink-0" />
			<div class="min-w-0">
				<div class="font-bold text-amber-200">Caja Cerrada</div>
				<div class="text-amber-400/80 truncate">Inicie la caja para poder cobrar</div>
			</div>
		</div>

		<button
			type="button"
			onclick={onOpenRegister}
			class="py-1 px-2.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-neutral-950 font-black text-xs flex items-center gap-1 transition active:scale-95 shrink-0 cursor-pointer shadow-xs"
		>
			<Store class="w-3.5 h-3.5" />
			<span>Abrir Caja</span>
		</button>
	</div>
{/if}
