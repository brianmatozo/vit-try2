<script lang="ts">
import { formatARS } from '@vitalcer/core';
import { Search } from 'lucide-svelte';

interface Props {
	isEmpty: boolean;
	totalUnits: number;
	totalAmount: number;
	onOpenSearch: () => void;
	onOpenCheckout: () => void;
}

let { isEmpty, totalUnits, totalAmount, onOpenSearch, onOpenCheckout }: Props =
	$props();
</script>

<footer class="fixed bottom-0 inset-x-0 max-w-md mx-auto p-3 bg-neutral-900/95 backdrop-blur-xl border-t border-neutral-800 z-40">
	<div class="flex items-center gap-2">
		<!-- Quick Search Catalog Button -->
		<button
			type="button"
			onclick={onOpenSearch}
			class="h-14 px-4 bg-neutral-800 hover:bg-neutral-700 active:scale-95 text-neutral-200 font-bold rounded-2xl border border-neutral-700 transition flex flex-col items-center justify-center gap-0.5 shrink-0 cursor-pointer"
		>
			<Search class="w-5 h-5 text-emerald-400" />
			<span class="text-2xs">Buscar</span>
		</button>

		<!-- Primary Checkout Button -->
		<button
			type="button"
			onclick={onOpenCheckout}
			disabled={isEmpty}
			class="flex-1 h-14 bg-emerald-600 hover:bg-emerald-500 disabled:bg-neutral-800 disabled:text-neutral-500 text-white font-black rounded-2xl shadow-lg shadow-emerald-600/25 disabled:shadow-none transition active:scale-[0.98] flex items-center justify-between px-5 cursor-pointer disabled:cursor-not-allowed"
		>
			<div class="text-left">
				<div class="text-2xs uppercase font-bold tracking-wider opacity-80 leading-none">
					{totalUnits} {totalUnits === 1 ? 'artículo' : 'artículos'}
				</div>
				<div class="text-sm font-extrabold leading-tight mt-0.5">
					Cobrar
				</div>
			</div>

			<div class="text-xl font-black tracking-tight text-white">
				{formatARS(totalAmount)}
			</div>
		</button>
	</div>
</footer>
