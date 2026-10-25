<script lang="ts">
import { Button, Dialog } from '@vitalcer/ui';
import { Trash2 } from 'lucide-svelte';

interface Props {
	open: boolean;
	onConfirm: () => void;
	onCancel: () => void;
}

let { open = $bindable(), onConfirm, onCancel }: Props = $props();
</script>

<Dialog
	bind:open
	title="¿Vaciar el carrito?"
	description="Se eliminarán todos los artículos actuales del carrito."
	position="center"
	class="max-w-xs"
>
	<div class="py-2 text-center space-y-3">
		<div class="w-12 h-12 rounded-full bg-rose-50 text-rose-600 border border-rose-200 flex items-center justify-center mx-auto">
			<Trash2 class="w-6 h-6" />
		</div>
	</div>
	{#snippet footer()}
		<Button
			variant="outline"
			size="sm"
			onclick={onCancel}
			class="flex-1"
		>
			Cancelar
		</Button>
		<Button
			variant="destructive"
			size="sm"
			onclick={onConfirm}
			class="flex-1"
		>
			Vaciar
		</Button>
	{/snippet}
</Dialog>
