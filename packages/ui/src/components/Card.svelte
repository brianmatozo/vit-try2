<script lang="ts">
import type { Snippet } from 'svelte';
import type { HTMLAttributes } from 'svelte/elements';
import { cn } from '../utils.js';

interface Props extends HTMLAttributes<HTMLDivElement> {
	children?: Snippet;
}

let { class: className = '', children, ...restProps }: Props = $props();
</script>

<div
  class={cn(
    'rounded-lg border border-gray-200 bg-white p-4 shadow-xs text-gray-900',
    className
  )}
  {...restProps}
>
  {@render children?.()}
</div>
