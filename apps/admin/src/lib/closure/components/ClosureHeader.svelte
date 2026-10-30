<script lang="ts">
import { Badge, Button } from '@vitalcer/ui';
import {
	ArrowDownUp,
	CheckCircle2,
	Clock,
	Lock,
	Plus,
	RefreshCw,
	Store,
} from 'lucide-svelte';
import { getClosureStatusBadge } from '../closure-filter.js';

interface Props {
	hasActiveClosure: boolean;
	activeStatus?: string;
	isRefreshing?: boolean;
	onOpenModal: () => void;
	onMovementModal: () => void;
	onArqueoModal: () => void;
	onRefresh: () => void;
}

let {
	hasActiveClosure,
	activeStatus,
	isRefreshing = false,
	onOpenModal,
	onMovementModal,
	onArqueoModal,
	onRefresh,
}: Props = $props();

const statusBadge = $derived(
	getClosureStatusBadge(hasActiveClosure ? activeStatus || 'open' : 'closed'),
);
</script>

<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-gray-200">
  <div class="space-y-1">
    <div class="flex items-center gap-2.5">
      <h1 class="text-xl sm:text-2xl font-bold tracking-tight text-gray-900">
        Cierre & Arqueo de Caja
      </h1>
      <Badge variant={statusBadge.variant}>
        {statusBadge.label}
      </Badge>
    </div>
    <div class="flex items-center gap-3 text-xs text-gray-500">
      <span class="flex items-center gap-1">
        <Clock class="size-3.5 text-gray-400" />
        Horario habitual: 09:00 a 20:30 ART
      </span>
      <span>•</span>
      <span class="flex items-center gap-1">
        <Store class="size-3.5 text-gray-400" />
        Turno Comercial
      </span>
    </div>
  </div>

  <div class="flex items-center gap-2 flex-wrap">
    <Button
      variant="outline"
      size="sm"
      onclick={onRefresh}
      disabled={isRefreshing}
      title="Actualizar datos"
    >
      <RefreshCw class="size-4 {isRefreshing ? 'animate-spin' : ''}" />
    </Button>

    {#if hasActiveClosure}
      <Button
        variant="outline"
        size="sm"
        onclick={onMovementModal}
        class="border-gray-300 text-gray-700"
      >
        <ArrowDownUp class="size-4 mr-1.5 text-amber-600" />
        Movimiento
      </Button>
      <Button
        variant="destructive"
        size="sm"
        onclick={onArqueoModal}
      >
        <Lock class="size-4 mr-1.5" />
        Cerrar Caja (Arqueo)
      </Button>
    {:else}
      <Button
        variant="primary"
        size="sm"
        onclick={onOpenModal}
      >
        <Plus class="size-4 mr-1.5" />
        Abrir Caja
      </Button>
    {/if}
  </div>
</div>
