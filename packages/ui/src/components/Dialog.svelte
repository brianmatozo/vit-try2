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
      class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs transition-opacity"
    />
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto pointer-events-none">
      <BitsDialog.Content
        class={cn(
          'pointer-events-auto relative w-full max-w-lg max-h-[90vh] flex flex-col rounded-lg border border-gray-200 bg-white p-6 shadow-xl text-gray-900 focus:outline-none overflow-y-auto',
          className
        )}
      >
        <div class="flex items-start justify-between mb-4 shrink-0">
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
            class="rounded-sm p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors cursor-pointer"
          >
            <X class="w-4 h-4" />
            <span class="sr-only">Cerrar</span>
          </BitsDialog.Close>
        </div>

        <div class="my-2 flex-1 overflow-y-auto">
          {@render children?.()}
        </div>

        {#if footer}
          <div class="mt-4 flex justify-end gap-2 pt-3 border-t border-gray-100 shrink-0">
            {@render footer()}
          </div>
        {/if}
      </BitsDialog.Content>
    </div>
  </BitsDialog.Portal>
</BitsDialog.Root>
