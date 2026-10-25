<script lang="ts">
import { AlertCircle, CheckCircle, Volume2 } from 'lucide-svelte';
import type { CounterNotification as NotificationType } from '../counter-state.svelte';

interface Props {
	notification: NotificationType | null;
}

let { notification }: Props = $props();
</script>

{#if notification}
	<div class="fixed top-14 inset-x-4 max-w-sm mx-auto z-50 pointer-events-none transition-all duration-300">
		<div class="px-4 py-2.5 rounded-2xl shadow-xl backdrop-blur-md flex items-center gap-2 text-xs font-bold border {notification.type === 'error' ? 'bg-rose-950/90 text-rose-200 border-rose-700' : notification.type === 'success' ? 'bg-emerald-950/90 text-emerald-200 border-emerald-700' : 'bg-neutral-900/90 text-neutral-200 border-neutral-700'}">
			{#if notification.type === 'error'}
				<AlertCircle class="w-4 h-4 text-rose-400 shrink-0" />
			{:else if notification.type === 'success'}
				<CheckCircle class="w-4 h-4 text-emerald-400 shrink-0" />
			{:else}
				<Volume2 class="w-4 h-4 text-neutral-400 shrink-0" />
			{/if}
			<span class="flex-1 truncate">{notification.message}</span>
		</div>
	</div>
{/if}
