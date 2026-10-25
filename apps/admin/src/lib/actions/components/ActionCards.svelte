<script lang="ts">
import { Button, Card } from '@vitalcer/ui';
import { PackagePlus, Sliders, Trash2 } from 'lucide-svelte';

interface Props {
	onOpenReceive: () => void;
	onOpenMerma: () => void;
	onOpenAdjust: () => void;
}

let { onOpenReceive, onOpenMerma, onOpenAdjust }: Props = $props();
</script>

<div class="grid grid-cols-1 md:grid-cols-3 gap-3.5 sm:gap-6">
  <!-- 1. Stock Inbound / Receiving -->
  <Card class="p-4 sm:p-5 flex flex-col justify-between hover:border-gray-300 transition-colors">
    <div>
      <div class="w-9 h-9 rounded-md bg-emerald-100 text-emerald-700 flex items-center justify-center mb-3 sm:mb-4">
        <PackagePlus class="w-5 h-5" />
      </div>
      <h2 class="text-base font-semibold text-gray-900">Recepción de Proveedor</h2>
      <p class="text-xs text-gray-500 mt-1">
        Ingreso de mercadería por remito, factura de proveedor o reposición de bultos. Aumenta el stock físico disponible.
      </p>
    </div>

    <div class="mt-5 sm:mt-6 pt-3 sm:pt-4 border-t border-gray-100">
      <Button
        class="w-full justify-center h-10 sm:h-9"
        onclick={onOpenReceive}
      >
        Registrar Ingreso
      </Button>
    </div>
  </Card>

  <!-- 2. Shrinkage / Merma -->
  <Card class="p-4 sm:p-5 flex flex-col justify-between hover:border-gray-300 transition-colors">
    <div>
      <div class="w-9 h-9 rounded-md bg-rose-100 text-rose-700 flex items-center justify-center mb-3 sm:mb-4">
        <Trash2 class="w-5 h-5" />
      </div>
      <h2 class="text-base font-semibold text-gray-900">Merma / Pérdida</h2>
      <p class="text-xs text-gray-500 mt-1">
        Baja justificada por rotura, deshidratación natural en frutos secos/legumbres, vencimiento o degustación en local.
      </p>
    </div>

    <div class="mt-5 sm:mt-6 pt-3 sm:pt-4 border-t border-gray-100">
      <Button
        variant="outline"
        class="w-full justify-center text-rose-700 hover:bg-rose-50 hover:border-rose-300 h-10 sm:h-9"
        onclick={onOpenMerma}
      >
        Registrar Merma
      </Button>
    </div>
  </Card>

  <!-- 3. Manual Audit Adjustment -->
  <Card class="p-4 sm:p-5 flex flex-col justify-between hover:border-gray-300 transition-colors">
    <div>
      <div class="w-9 h-9 rounded-md bg-amber-100 text-amber-700 flex items-center justify-center mb-3 sm:mb-4">
        <Sliders class="w-5 h-5" />
      </div>
      <h2 class="text-base font-semibold text-gray-900">Ajuste por Auditoría Física</h2>
      <p class="text-xs text-gray-500 mt-1">
        Conciliación de inventario ante recuentos. Registra el delta en lista general sin sobreescritura directa.
      </p>
    </div>

    <div class="mt-5 sm:mt-6 pt-3 sm:pt-4 border-t border-gray-100">
      <Button
        variant="outline"
        class="w-full justify-center text-amber-700 hover:bg-amber-50 hover:border-amber-300 h-10 sm:h-9"
        onclick={onOpenAdjust}
      >
        Conciliar Stock
      </Button>
    </div>
  </Card>
</div>
