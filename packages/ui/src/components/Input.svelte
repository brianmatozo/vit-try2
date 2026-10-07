<script lang="ts">
import type { HTMLInputAttributes } from 'svelte/elements';
import { cn } from '../utils.js';

interface Props extends HTMLInputAttributes {
	value?: string | number;
}

let {
	class: className = '',
	value = $bindable(''),
	...restProps
}: Props = $props();
</script>

<input
  bind:value
  class={cn(
    'flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-base sm:text-sm placeholder:text-gray-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:border-transparent disabled:cursor-not-allowed disabled:opacity-50',
    className
  )}
  {...restProps}
/>
