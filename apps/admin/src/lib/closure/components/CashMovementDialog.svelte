<script lang="ts">
import { Button, Dialog, Input } from '@vitalcer/ui';
import { ArrowDownLeft, ArrowUpRight, TrendingUp } from 'lucide-svelte';

interface Props {
	open: boolean;
	closureId: number;
	isSubmitting?: boolean;
	onClose: () => void;
	onConfirm: (
		movementType: 'cash_in' | 'cash_out',
		amount: number,
		reason: string,
	) => Promise<void>;
}

let {
	open = $bindable(false),
	closureId,
	isSubmitting = false,
	onClose,
	onConfirm,
}: Props = $props();

let movementType = $state<'cash_out' | 'cash_in'>('cash_out');
let amount = $state(2000);
let reason = $state('');

const COMMON_REASONS = [
	'Cadetería / Moto',
	'Artículos de Limpieza',
	'Ingreso de Cambio Chico',
	'Retiro a Caja Fuerte',
	'Insumos / Bolsas',
];

async function handleSubmit(e: SubmitEvent) {
	e.preventDefault();
	if (!reason.trim()) return;
	await onConfirm(
		movementType,
		Math.max(1, Math.round(amount || 0)),
		reason.trim(),
	);
}
</script>

<Dialog
  bind:open
  centered
  title="Registrar Movimiento de Cajón"
  description="Registre salidas o ingresos excepcionales de efectivo durante el turno."
>
  <form id="cash-movement-form" onsubmit={handleSubmit} class="space-y-4 py-2">
    <div>
      <span class="block text-xs font-semibold text-gray-700 uppercase tracking-wide mb-1.5">
        Tipo de Movimiento
      </span>
      <div class="grid grid-cols-2 gap-2">
        <button
          type="button"
          onclick={() => { movementType = 'cash_out'; }}
          class="flex items-center justify-center gap-1.5 py-2 px-3 text-xs font-bold rounded-lg border transition-all {movementType === 'cash_out' ? 'bg-rose-50 border-rose-500 text-rose-700 shadow-xs' : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'}"
        >
          <ArrowDownLeft class="size-4" />
          Egreso / Gasto
        </button>
        <button
          type="button"
          onclick={() => { movementType = 'cash_in'; }}
          class="flex items-center justify-center gap-1.5 py-2 px-3 text-xs font-bold rounded-lg border transition-all {movementType === 'cash_in' ? 'bg-emerald-50 border-emerald-500 text-emerald-700 shadow-xs' : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'}"
        >
          <ArrowUpRight class="size-4" />
          Ingreso Extra
        </button>
      </div>
    </div>

    <div>
      <label for="movement-amount" class="block text-xs font-semibold text-gray-700 uppercase tracking-wide mb-1.5">
        Monto ($ ARS)
      </label>
      <Input
        id="movement-amount"
        type="number"
        min="1"
        step="100"
        bind:value={amount}
        placeholder="Ej: 3500"
        required
        class="text-base font-semibold"
      />
    </div>

    <div>
      <label for="movement-reason" class="block text-xs font-semibold text-gray-700 uppercase tracking-wide mb-1.5">
        Motivo / Detalle
      </label>
      <input
        id="movement-reason"
        type="text"
        bind:value={reason}
        placeholder="Ej: Pago de flete a proveedor"
        required
        class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white text-gray-900"
      />
      <div class="flex flex-wrap gap-1.5 mt-2">
        {#each COMMON_REASONS as common}
          <button
            type="button"
            onclick={() => { reason = common; }}
            class="text-2xs px-2 py-0.5 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-700 transition-colors"
          >
            {common}
          </button>
        {/each}
      </div>
    </div>
  </form>

  {#snippet footer()}
    <div class="flex items-center w-full justify-between gap-2">
      <Button
        variant="outline"
        size="sm"
        onclick={onClose}
        disabled={isSubmitting}
        class="mr-auto"
      >
        Cancelar
      </Button>
      <Button
        type="submit"
        form="cash-movement-form"
        variant={movementType === 'cash_out' ? 'destructive' : 'primary'}
        size="sm"
        disabled={isSubmitting || !reason.trim() || amount <= 0}
      >
        {isSubmitting ? 'Guardando...' : 'Confirmar Movimiento'}
      </Button>
    </div>
  {/snippet}
</Dialog>
