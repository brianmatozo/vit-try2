<script lang="ts">
import { Button, Dialog, Input } from '@vitalcer/ui';
import { AlertCircle } from 'lucide-svelte';
import type { ProductFormState } from '../product-form.svelte';

interface Props {
	form: ProductFormState;
	isSubmitting: boolean;
	onSubmit: (e: SubmitEvent) => void;
}

let { form, isSubmitting, onSubmit }: Props = $props();
</script>

<Dialog
  bind:open={form.isOpen}
  title={form.dialogTitle}
  description={form.dialogDescription}
>
  <form id="productForm" onsubmit={onSubmit} class="space-y-4">
    {#if form.formError}
      <div class="p-2.5 bg-rose-50 border border-rose-200 rounded-md flex items-center gap-2 text-rose-800 text-xs">
        <AlertCircle class="w-4 h-4 text-rose-600 shrink-0" />
        <span>{form.formError}</span>
      </div>
    {/if}

    <!-- Basic Info -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <div>
        <label for="prod-sku" class="block text-xs font-semibold text-gray-700 mb-1">
          PLU / Código de Barras *
        </label>
        <Input
          id="prod-sku"
          placeholder="Ej: 7791234567890 o ALF-01"
          bind:value={form.sku}
          required
        />
      </div>

      <div>
        <label for="prod-type" class="block text-xs font-semibold text-gray-700 mb-1">
          Tipo de Artículo *
        </label>
        <select
          id="prod-type"
          bind:value={form.productType}
          class="w-full h-10 sm:h-9 rounded-md border border-gray-300 bg-white px-3 py-1 text-base sm:text-sm text-gray-900 shadow-xs focus:outline-none focus:border-emerald-600"
        >
          <option value="discrete">Unidad (Discreto)</option>
          <option value="bulk">Pesable / Granel (Balanza)</option>
        </select>
      </div>
    </div>

    <div>
      <label for="prod-name" class="block text-xs font-semibold text-gray-700 mb-1">
        Nombre del Producto *
      </label>
      <Input
        id="prod-name"
        placeholder="Ej: Almendras Nonpareil o Alfajor Choco"
        bind:value={form.name}
        required
      />
    </div>

    <!-- Bulk specific fields -->
    {#if form.productType === 'bulk'}
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3 bg-emerald-50/50 rounded-lg border border-emerald-100">
        <div>
          <label for="prod-plu" class="block text-xs font-semibold text-emerald-900 mb-1">
            Código PLU Balanza (4 dígitos)
          </label>
          <Input
            id="prod-plu"
            maxlength={4}
            placeholder="Ej: 0142"
            bind:value={form.pluCode}
          />
          <span class="text-2xs text-emerald-700 mt-0.5 block">Para balanza EAN-13 (prefijo 20)</span>
        </div>

        <div>
          <label for="prod-ref-grams" class="block text-xs font-semibold text-emerald-900 mb-1">
            Gramos de Referencia
          </label>
          <Input
            id="prod-ref-grams"
            type="number"
            min="1"
            bind:value={form.bulkReferenceGrams}
            required
          />
          <span class="text-2xs text-emerald-700 mt-0.5 block">Precio cada N gramos (ej: 100g)</span>
        </div>
      </div>
    {/if}

    <!-- Pricing & Initial Stock / Buffer -->
    <div class="grid grid-cols-1 {!form.isEditing ? 'sm:grid-cols-3' : 'sm:grid-cols-2'} gap-3">
      <div>
        <label for="prod-price" class="block text-xs font-semibold text-gray-700 mb-1">
          {form.productType === 'bulk' ? `Precio / ${form.bulkReferenceGrams}g ($ ARS) *` : 'Precio / Unidad ($ ARS) *'}
        </label>
        <Input
          id="prod-price"
          type="number"
          min="1"
          placeholder="Ej: 1500"
          bind:value={form.unitPrice}
          required
        />
      </div>

      {#if !form.isEditing}
        <div>
          <label for="prod-stock" class="block text-xs font-semibold text-gray-700 mb-1">
            Stock Inicial ({form.productType === 'bulk' ? 'Gramos' : 'Unidades'})
          </label>
          <Input
            id="prod-stock"
            type="number"
            min="0"
            bind:value={form.initialStock}
          />
        </div>
      {/if}

      <div>
        <label for="prod-buffer" class="block text-xs font-semibold text-gray-700 mb-1">
          Buffer Seguridad (Delivery)
        </label>
        <Input
          id="prod-buffer"
          type="number"
          min="0"
          placeholder="0"
          bind:value={form.minSafetyBuffer}
        />
        <span class="text-2xs text-gray-500 mt-0.5 block">Reserva no publicada en apps</span>
      </div>
    </div>

    <!-- Status & Channels -->
    <div class="pt-2 border-t border-gray-100 space-y-2.5">
      <label class="flex items-center gap-2 cursor-pointer text-xs font-semibold text-gray-800">
        <input
          type="checkbox"
          bind:checked={form.isActive}
          class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500 w-4 h-4"
        />
        <span>Artículo Activo / Disponible para venta</span>
      </label>

      <div>
        <div class="text-xs text-gray-500 font-medium mb-1.5">Sincronización con canales de delivery:</div>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs text-gray-700">
          <label class="flex items-center gap-1.5 p-2 rounded-md border border-gray-200 bg-gray-50/50 hover:bg-gray-50 cursor-pointer transition-colors">
            <input type="checkbox" bind:checked={form.syncPedidosya} class="rounded border-gray-300 text-emerald-600 w-3.5 h-3.5" />
            <span>PedidosYa</span>
          </label>
          <label class="flex items-center gap-1.5 p-2 rounded-md border border-gray-200 bg-gray-50/50 hover:bg-gray-50 cursor-pointer transition-colors">
            <input type="checkbox" bind:checked={form.syncRappi} class="rounded border-gray-300 text-emerald-600 w-3.5 h-3.5" />
            <span>Rappi</span>
          </label>
          <label class="flex items-center gap-1.5 p-2 rounded-md border border-gray-200 bg-gray-50/50 hover:bg-gray-50 cursor-pointer transition-colors">
            <input type="checkbox" bind:checked={form.syncVgo} class="rounded border-gray-300 text-emerald-600 w-3.5 h-3.5" />
            <span>VGO</span>
          </label>
          <label class="flex items-center gap-1.5 p-2 rounded-md border border-gray-200 bg-gray-50/50 hover:bg-gray-50 cursor-pointer transition-colors">
            <input type="checkbox" bind:checked={form.syncMercadolibre} class="rounded border-gray-300 text-emerald-600 w-3.5 h-3.5" />
            <span>MercadoLibre</span>
          </label>
        </div>
      </div>
    </div>
  </form>

  {#snippet footer()}
    <Button
      variant="outline"
      size="sm"
      type="button"
      class="flex-1 sm:flex-none justify-center"
      onclick={() => form.close()}
    >
      Cancelar
    </Button>
    <Button
      size="sm"
      type="submit"
      form="productForm"
      class="flex-1 sm:flex-none justify-center"
      disabled={isSubmitting}
    >
      {isSubmitting ? 'Guardando...' : (form.isEditing ? 'Guardar Cambios' : 'Crear Producto')}
    </Button>
  {/snippet}
</Dialog>
