<script lang="ts">
import { Button, Dialog, Input } from '@vitalcer/ui';
import { Coins, Sparkles } from 'lucide-svelte';

interface Props {
	open: boolean;
	isSubmitting?: boolean;
	onClose: () => void;
	onConfirm: (initialCash: number, notes?: string) => Promise<void>;
}

let {
	open = $bindable(false),
	isSubmitting = false,
	onClose,
	onConfirm,
}: Props = $props();

let initialCash = $state(20000);
let notes = $state('');

const PRESETS = [0, 10000, 20000, 50000];

async function handleSubmit(e: SubmitEvent) {
	e.preventDefault();
	await onConfirm(Math.max(0, Math.round(initialCash || 0)), notes.trim());
}
</script>

<Dialog
  bind:open
  centered
  title="Abrir Sesión de Caja"
  description="Ingrese el fondo de cambio inicial para comenzar a cobrar ventas."
>
  <form id="open-closure-form" onsubmit={handleSubmit} class="space-y-4 py-2">
    <div>
      <label for="initial-cash" class="block text-xs font-semibold text-gray-700 uppercase tracking-wide mb-1.5">
        Fondo Inicial en Efectivo ($ ARS)
      </label>
      <Input
        id="initial-cash"
        type="number"
        min="0"
        step="100"
        bind:value={initialCash}
        placeholder="Ej: 20000"
        required
        class="text-base font-semibold"
      />
    </div>

    <div>
      <span class="block text-xs text-gray-500 mb-1.5 font-medium">Valores habituales:</span>
      <div class="grid grid-cols-4 gap-2">
        {#each PRESETS as preset}
          <button
            type="button"
            onclick={() => { initialCash = preset; }}
            class="py-1.5 px-2 text-xs font-semibold rounded-lg border transition-colors {initialCash === preset ? 'bg-emerald-50 border-emerald-500 text-emerald-700' : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'}"
          >
            {preset === 0 ? '$0' : `$${preset.toLocaleString('es-AR')}`}
          </button>
        {/each}
      </div>
    </div>

    <div>
      <label for="open-notes" class="block text-xs font-semibold text-gray-700 uppercase tracking-wide mb-1.5">
        Observaciones de Apertura (Opcional)
      </label>
      <input
        id="open-notes"
        type="text"
        bind:value={notes}
        placeholder="Ej: Turno mañana, cambio chico cargado"
        class="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white text-gray-900"
      />
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
        form="open-closure-form"
        variant="primary"
        size="sm"
        disabled={isSubmitting}
      >
        <Sparkles class="size-4 mr-1.5" />
        {isSubmitting ? 'Abriendo...' : 'Confirmar Apertura'}
      </Button>
    </div>
  {/snippet}
</Dialog>
