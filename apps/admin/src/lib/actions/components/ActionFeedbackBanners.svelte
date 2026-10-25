<script lang="ts">
import { Card } from '@vitalcer/ui';
import { AlertCircle, CheckCircle2 } from 'lucide-svelte';
import type { ActionSuccessBanner } from '../actions-state.svelte';

interface Props {
	successBanner: ActionSuccessBanner | null;
	errorMessage: string | null;
	onDismissSuccess: () => void;
	onDismissError: () => void;
}

let { successBanner, errorMessage, onDismissSuccess, onDismissError }: Props =
	$props();
</script>

{#if successBanner}
  <Card class="p-3 sm:p-4 bg-emerald-50 border-emerald-200">
    <div class="flex items-start justify-between">
      <div class="flex items-start gap-2.5 sm:gap-3">
        <CheckCircle2 class="w-5 h-5 text-emerald-600 mt-0.5 shrink-0" />
        <div>
          <h3 class="text-sm font-semibold text-emerald-900">{successBanner.title}</h3>
          <p class="text-xs text-emerald-700 mt-0.5">{successBanner.description}</p>
          {#if successBanner.ledger}
            <p class="text-xs font-mono text-emerald-800 mt-1">
              Asiento Entrada #{successBanner.ledger.id} &bull; Δ: {successBanner.ledger.quantity_delta > 0 ? `+${successBanner.ledger.quantity_delta}` : successBanner.ledger.quantity_delta} &bull; Saldo posterior: {successBanner.ledger.balance_after}
            </p>
          {/if}
        </div>
      </div>
      <button
        type="button"
        onclick={onDismissSuccess}
        class="text-xs text-emerald-600 hover:text-emerald-800 cursor-pointer p-1"
      >
        Cerrar
      </button>
    </div>
  </Card>
{/if}

{#if errorMessage}
  <Card class="p-3 sm:p-4 bg-rose-50 border-rose-200">
    <div class="flex items-start justify-between">
      <div class="flex items-start gap-2.5 sm:gap-3">
        <AlertCircle class="w-5 h-5 text-rose-600 mt-0.5 shrink-0" />
        <div>
          <h3 class="text-sm font-semibold text-rose-900">Error en la operación</h3>
          <p class="text-xs text-rose-700 mt-0.5">{errorMessage}</p>
        </div>
      </div>
      <button
        type="button"
        onclick={onDismissError}
        class="text-xs text-rose-600 hover:text-rose-800 cursor-pointer p-1"
      >
        Cerrar
      </button>
    </div>
  </Card>
{/if}
