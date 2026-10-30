<script lang="ts">
import { recordCashMovement } from '@vitalcer/api';
import { formatARS } from '@vitalcer/core';
import { Button, Dialog, Input } from '@vitalcer/ui';
import {
	AlertCircle,
	ArrowDownRight,
	ArrowUpRight,
	Loader2,
} from 'lucide-svelte';
import { playSuccess } from '$lib/audio/sound';

interface Props {
	open: boolean;
	activeClosureId: number;
	onMovementSuccess: () => void;
	onCancel: () => void;
}

let {
	open = $bindable(false),
	activeClosureId,
	onMovementSuccess,
	onCancel,
}: Props = $props();

let movementType = $state<'cash_out' | 'cash_in'>('cash_out');
let amount = $state<number>(0);
let reason = $state<string>('');
let isSubmitting = $state<boolean>(false);
let errorMessage = $state<string | null>(null);

const reasons = [
	'Artículos de limpieza',
	'Pago a cadete / flete',
	'Bolsas e insumos',
	'Cambio de billetes',
];

async function handleConfirm() {
	if (amount <= 0) {
		errorMessage = 'El monto debe ser mayor a $0';
		return;
	}
	if (!reason.trim()) {
		errorMessage = 'Debe indicar el concepto o motivo del movimiento';
		return;
	}

	isSubmitting = true;
	errorMessage = null;

	try {
		const res = await recordCashMovement({
			path: { closure_id: activeClosureId },
			body: {
				movement_type: movementType,
				amount: Math.round(amount),
				reason: reason.trim(),
			},
		});

		if (res.error) {
			const err = res.error as { detail?: string };
			throw new Error(err.detail || 'Error al registrar el movimiento');
		}

		await playSuccess()?.catch?.(() => {});
		open = false;
		amount = 0;
		reason = '';
		onMovementSuccess();
	} catch (err: unknown) {
		const error = err as Error;
		errorMessage = error.message || 'Error al registrar el movimiento de caja';
	} finally {
		isSubmitting = false;
	}
}
</script>

<Dialog
	bind:open
	title="Movimiento de Caja"
	description="Registre retiros, gastos o ingresos de efectivo del cajón."
	class="max-w-md"
>
	<div class="space-y-4 pt-2">
		<!-- Type Switcher -->
		<div class="grid grid-cols-2 gap-2">
			<button
				type="button"
				onclick={() => (movementType = 'cash_out')}
				class="p-2.5 rounded-xl border flex items-center justify-center gap-1.5 transition text-xs font-bold cursor-pointer {movementType === 'cash_out' ? 'bg-rose-50 border-rose-500 text-rose-800 shadow-2xs' : 'bg-white border-neutral-200 text-neutral-600'}"
			>
				<ArrowDownRight class="w-4 h-4 text-rose-600" />
				Gasto / Retiro
			</button>
			<button
				type="button"
				onclick={() => (movementType = 'cash_in')}
				class="p-2.5 rounded-xl border flex items-center justify-center gap-1.5 transition text-xs font-bold cursor-pointer {movementType === 'cash_in' ? 'bg-emerald-50 border-emerald-500 text-emerald-800 shadow-2xs' : 'bg-white border-neutral-200 text-neutral-600'}"
			>
				<ArrowUpRight class="w-4 h-4 text-emerald-600" />
				Ingreso Extra
			</button>
		</div>

		<!-- Amount Input -->
		<div class="space-y-1">
			<label for="movement-amount-input" class="block text-xs font-bold text-neutral-700">
				Monto en Efectivo
			</label>
			<div class="relative">
				<span class="absolute left-3.5 top-1/2 -translate-y-1/2 text-lg font-bold text-neutral-400">$</span>
				<Input
					id="movement-amount-input"
					type="number"
					min="0"
					step="100"
					bind:value={amount}
					class="pl-8 text-xl font-black h-12 rounded-xl text-neutral-900"
				/>
			</div>
			<div class="text-xs text-neutral-500">Monto: {formatARS(amount)}</div>
		</div>

		<!-- Concept / Reason -->
		<div class="space-y-1.5">
			<label for="movement-reason-input" class="block text-xs font-bold text-neutral-700">
				Motivo / Concepto
			</label>
			<Input
				id="movement-reason-input"
				type="text"
				placeholder="Ej: Bolsas, flete, viáticos..."
				bind:value={reason}
				class="text-sm rounded-xl text-neutral-900"
			/>
			<div class="flex flex-wrap gap-1 pt-1">
				{#each reasons as r}
					<button
						type="button"
						onclick={() => (reason = r)}
						class="text-xs py-1 px-2 rounded-md bg-neutral-100 hover:bg-neutral-200 text-neutral-700 font-medium cursor-pointer"
					>
						{r}
					</button>
				{/each}
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
				class="w-2/3 {movementType === 'cash_out' ? 'bg-rose-600 hover:bg-rose-700' : 'bg-emerald-600 hover:bg-emerald-700'} text-white font-bold"
				disabled={isSubmitting}
				onclick={handleConfirm}
			>
				{#if isSubmitting}
					<Loader2 class="w-4 h-4 animate-spin mr-1.5" />
					Guardando...
				{:else}
					Registrar {movementType === 'cash_out' ? 'Gasto' : 'Ingreso'}
				{/if}
			</Button>
		</div>
	</div>
</Dialog>
