<script lang="ts">
import { ARGENTINE_BANKNOTES, type BanknoteDenomination } from '@vitalcer/core';
import { Badge, Button, Dialog } from '@vitalcer/ui';
import { CheckCircle2, Lock, Minus, Plus } from 'lucide-svelte';
import { ArqueoState } from '../arqueo-state.svelte.js';
import {
	formatCurrencyARS,
	getDiscrepancyBadgeInfo,
} from '../closure-filter.js';

interface Props {
	open: boolean;
	closureId: number;
	expectedCash: number;
	isSubmitting?: boolean;
	onClose: () => void;
	onConfirm: (
		closureId: number,
		countedCash: number,
		breakdown: Record<number, number>,
		notes?: string,
	) => Promise<void>;
}

let {
	open = $bindable(false),
	closureId,
	expectedCash,
	isSubmitting = false,
	onClose,
	onConfirm,
}: Props = $props();

const arqueo = new ArqueoState(0);

$effect(() => {
	if (open) {
		arqueo.reset(expectedCash);
	}
});

const discrepancyBadge = $derived(
	getDiscrepancyBadgeInfo(expectedCash, arqueo.totalCounted),
);

async function handleCloseSession() {
	await onConfirm(
		closureId,
		arqueo.totalCounted,
		arqueo.counts,
		arqueo.notes.trim() || undefined,
	);
}
</script>

<Dialog
  bind:open
  centered
  title="Arqueo de Efectivo & Cierre de Caja"
  description="Cuente los billetes físicos del cajón para comparar contra el saldo del sistema."
>
  <div class="space-y-4 py-2">
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
      {#each ARGENTINE_BANKNOTES as denom}
        {@const count = arqueo.counts[denom] || 0}
        <div class="border border-gray-200 rounded-lg p-2 bg-gray-50 flex flex-col justify-between">
          <div class="flex items-center justify-between text-xs font-semibold text-gray-700">
            <span>${denom.toLocaleString('es-AR')}</span>
            <span class="text-2xs text-gray-500 font-normal">${(denom * count).toLocaleString('es-AR')}</span>
          </div>
          <div class="flex items-center justify-between mt-1.5 gap-1">
            <button
              type="button"
              onclick={() => arqueo.decrementDenom(denom)}
              class="size-6 rounded bg-white border border-gray-200 flex items-center justify-center text-gray-600 hover:bg-gray-100 transition-colors"
            >
              <Minus class="size-3" />
            </button>
            <span class="text-xs font-bold text-gray-900 w-6 text-center">{count}</span>
            <button
              type="button"
              onclick={() => arqueo.incrementDenom(denom)}
              class="size-6 rounded bg-white border border-gray-200 flex items-center justify-center text-gray-600 hover:bg-gray-100 transition-colors"
            >
              <Plus class="size-3" />
            </button>
          </div>
        </div>
      {/each}
    </div>

    <div class="bg-gray-100/80 rounded-xl p-3 border border-gray-200 space-y-2">
      <div class="flex items-center justify-between text-xs">
        <span class="text-gray-600">Saldo Esperado en Cajón:</span>
        <span class="font-bold text-gray-900">{formatCurrencyARS(expectedCash)}</span>
      </div>
      <div class="flex items-center justify-between text-xs">
        <span class="text-gray-600">Total Físico Recontado:</span>
        <span class="font-bold text-emerald-700 text-sm">{formatCurrencyARS(arqueo.totalCounted)}</span>
      </div>
      <div class="flex items-center justify-between pt-1.5 border-t border-gray-200 text-xs">
        <span class="font-medium text-gray-700">Discrepancia:</span>
        <Badge variant={discrepancyBadge.variant}>
          {discrepancyBadge.label}
        </Badge>
      </div>
    </div>

    <div>
      <label for="arqueo-notes" class="block text-2xs font-semibold text-gray-600 uppercase mb-1">
        Observaciones de Cierre (Opcional)
      </label>
      <input
        id="arqueo-notes"
        type="text"
        bind:value={arqueo.notes}
        placeholder="Ej: Faltó billete de $1000 roto o diferencia de cambio"
        class="w-full px-2.5 py-1.5 text-xs rounded-lg border border-gray-300 focus:outline-none focus:ring-1 focus:ring-emerald-500 bg-white text-gray-900"
      />
    </div>
  </div>

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
        variant="destructive"
        size="sm"
        onclick={handleCloseSession}
        disabled={isSubmitting}
      >
        <Lock class="size-4 mr-1.5" />
        {isSubmitting ? 'Cerrando...' : 'Confirmar Cierre de Caja'}
      </Button>
    </div>
  {/snippet}
</Dialog>
