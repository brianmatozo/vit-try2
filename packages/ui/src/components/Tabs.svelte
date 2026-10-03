<script lang="ts">
import { Tabs as BitsTabs } from 'bits-ui';
import type { Snippet } from 'svelte';
import { cn } from '../utils.js';

export interface TabItem {
	id: string;
	label: string;
}

export interface TabsProps {
	value?: string;
	tabs: TabItem[];
	children?: Snippet;
	class?: string;
}

let {
	value = $bindable(''),
	tabs,
	children,
	class: className = '',
}: TabsProps = $props();

$effect(() => {
	if (!value && tabs.length > 0) {
		value = tabs[0].id;
	}
});
</script>

<BitsTabs.Root bind:value class={cn('w-full', className)}>
  <BitsTabs.List class="flex border-b border-gray-200 gap-1 mb-6 select-none">
    {#each tabs as tab (tab.id)}
      <BitsTabs.Trigger
        value={tab.id}
        class="px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-900 border-b-2 border-transparent data-[state=active]:border-emerald-600 data-[state=active]:text-emerald-700 transition-colors cursor-pointer focus:outline-none -mb-px"
      >
        {tab.label}
      </BitsTabs.Trigger>
    {/each}
  </BitsTabs.List>

  {@render children?.()}
</BitsTabs.Root>
