<script lang="ts">
import { openClosure } from '@vitalcer/api';
import { formatARS } from '@vitalcer/core';
import { Button, Dialog, Input } from '@vitalcer/ui';
import { AlertCircle, Loader2, Store } from 'lucide-svelte';
import { playSuccess } from '$lib/audio/sound';

interface Props {
	open: boolean;
	onOpenSuccess: () => void;
	onCancel: () => void;
}

let { open = $bindable(false), onOpenSuccess, onCancel }: Props = $props();

let initialCash = $state<number>(0);
let notes = $state<string>('');
let isSubmitting = $state<boolean>(false);
let errorMessage = $state<string | null>(null);

function handleSetAmount(amount: number) {
	initialCash = amount;
}

async function handleConfirmOpen() {
	isSubmitting = true;
	errorMessage = null;

	try {
		const res = await openClosure({
			body: {
				initial_cash: Math.max(0, Math.round(initialCash)),
				notes: notes.trim() || undefined,
			},
		});

		if (res.error) {
			const err = res.error as { detail?: string };
			throw new Error(err.detail || 'Error al abrir la caja');
		}

		await playSuccess()?.catch?.(() => {});
		open = false;
		initialCash = 0;
		notes = '';
		onOpenSuccess();
	} catch (err: unknown) {
		const error = err as Error;
		errorMessage = error.message || 'Error al iniciar la sesión de caja';
	} finally {
		isSubmitting = false;
	}
}
</script>

<Dialog
	bind:open
	title="Apertura de Caja"
	description="Ingrese el fondo de efectivo inicial para comenzar a operar."
	class="max-w-md"
>
	<div class="space-y-4 pt-2">
		<div class="space-y-1.5">
			<label for="initial-cash-input" class="block text-xs font-bold text-neutral-700">
				Fondo Inicial de Caja
			</label>
			<div class="relative">
				<span class="absolute left-3.5 top-1/2 -translate-y-1/2 text-lg font-bold text-neutral-400">$</span>
				<Input
					id="initial-cash-input"
					type="number"
					min="0"
					step="1000"
					bind:value={initialCash}
					class="pl-8 text-xl font-black h-12 rounded-xl text-neutral-900"
				/>
			</div>
			<div class="text-xs text-neutral-500">Monto actual: {formatARS(initialCash)}</div>
		</div>

		<!-- Quick presets -->
		<div class="space-y-1.5">
			<div class="text-xs font-semibold text-neutral-500">Montos sugeridos:</div>
			<div class="grid grid-cols-4 gap-1.5">
				<button
					type="button"
					onclick={() => handleSetAmount(0)}
					class="py-2 px-1 bg-white hover:bg-neutral-100 active:scale-95 text-xs font-bold text-neutral-800 rounded-lg border border-neutral-200 shadow-2xs cursor-pointer"
				>
					$0
				</button>
				<button
					type="button"
					onclick={() => handleSetAmount(10000)}
					class="py-2 px-1 bg-white hover:bg-neutral-100 active:scale-95 text-xs font-bold text-neutral-800 rounded-lg border border-neutral-200 shadow-2xs cursor-pointer"
				>
					$10.000
				</button>
				<button
					type="button"
					onclick={() => handleSetAmount(20000)}
					class="py-2 px-1 bg-white hover:bg-neutral-100 active:scale-95 text-xs font-bold text-neutral-800 rounded-lg border border-neutral-200 shadow-2xs cursor-pointer"
				>
					$20.000
				</button>
				<button
					type="button"
					onclick={() => handleSetAmount(50000)}
					class="py-2 px-1 bg-white hover:bg-neutral-100 active:scale-95 text-xs font-bold text-neutral-800 rounded-lg border border-neutral-200 shadow-2xs cursor-pointer"
				>
					$50.000
				</button>
			</div>
		</div>

		{#if errorMessage}
			<div class="p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-2 text-rose-800 text-xs font-semibold">
				<AlertCircle class="w-4 h-4 text-rose-600 shrink-0" />
				<span>{errorMessage}</span>
			</div>
		{/if}

		<div class="pt-2 flex items-center gap-2">
			<Button
				variant="outline"
				class="w-1/3"
				disabled={isSubmitting}
				onclick={() => {
					open = false;
					onCancel();
				}}
			>
				Cancelar
			</Button>
			<Button
				class="w-2/3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold"
				disabled={isSubmitting}
				onclick={handleConfirmOpen}
			>
				{#if isSubmitting}
					<Loader2 class="w-4 h-4 animate-spin mr-1.5" />
					Iniciando...
				{:else}
					<Store class="w-4 h-4 mr-1.5" />
					Abrir Caja
				{/if}
			</Button>
		</div>
	</div>
</Dialog>
