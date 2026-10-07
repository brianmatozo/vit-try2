<script lang="ts">
import { Dialog as BitsDialog } from 'bits-ui';
import { X } from 'lucide-svelte';
import type { Snippet } from 'svelte';
import { cn } from '../utils.js';

interface Props {
	open?: boolean;
	title: string;
	description?: string;
	children?: Snippet;
	footer?: Snippet;
	class?: string;
}

let {
	open = $bindable(false),
	title,
	description,
	children,
	footer,
	class: className = '',
}: Props = $props();
</script>

<BitsDialog.Root bind:open>
  <BitsDialog.Portal>
    <BitsDialog.Overlay
      class="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs transition-opacity"
    />
    <BitsDialog.Content
      class={cn(
        'fixed inset-x-0 bottom-0 z-50 flex max-h-[92dvh] w-full flex-col rounded-t-2xl border-t border-x border-gray-200 bg-white p-4 pb-6 shadow-2xl text-gray-900 focus:outline-none sm:inset-auto sm:left-1/2 sm:top-1/2 sm:-translate-x-1/2 sm:-translate-y-1/2 sm:w-[calc(100%-2rem)] sm:max-w-lg sm:max-h-[88dvh] sm:rounded-xl sm:border sm:p-6',
        className
      )}
    >
      <!-- Mobile bottom-sheet drag handle indicator -->
      <div class="w-10 h-1 bg-gray-300 rounded-full mx-auto mb-2.5 sm:hidden shrink-0"></div>

      <div class="flex items-start justify-between mb-3 shrink-0">
        <div>
          <BitsDialog.Title class="text-base font-semibold text-gray-900">
            {title}
          </BitsDialog.Title>
          {#if description}
            <BitsDialog.Description class="text-xs text-gray-500 mt-0.5">
              {description}
            </BitsDialog.Description>
          {/if}
        </div>
        <BitsDialog.Close
          class="rounded-md p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors cursor-pointer -mr-1 -mt-1"
        >
          <X class="w-5 h-5 sm:w-4 sm:h-4" />
          <span class="sr-only">Cerrar</span>
        </BitsDialog.Close>
      </div>

      <div class="my-1 flex-1 overflow-y-auto overscroll-contain min-h-0 pr-1">
        {@render children?.()}
      </div>

      {#if footer}
        <div class="mt-3 flex flex-wrap justify-end gap-2 pt-3 border-t border-gray-100 shrink-0">
          {@render footer()}
        </div>
      {/if}
    </BitsDialog.Content>
  </BitsDialog.Portal>
</BitsDialog.Root>
