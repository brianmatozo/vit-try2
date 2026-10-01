<script lang="ts">
import type { Snippet } from 'svelte';
import type { HTMLAttributes } from 'svelte/elements';
import { cn } from '../utils.js';

interface Props extends HTMLAttributes<HTMLSpanElement> {
	variant?: 'default' | 'success' | 'warning' | 'destructive' | 'outline';
	children?: Snippet;
}

let {
	variant = 'default',
	class: className = '',
	children,
	...restProps
}: Props = $props();

const variantClasses = {
	default: 'bg-gray-100 text-gray-800 border-gray-200',
	success: 'bg-emerald-50 text-emerald-700 border-emerald-200',
	warning: 'bg-amber-50 text-amber-700 border-amber-200',
	destructive: 'bg-rose-50 text-rose-700 border-rose-200',
	outline: 'border border-gray-300 text-gray-700',
};
</script>

<span
  class={cn(
    'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border',
    variantClasses[variant],
    className
  )}
  {...restProps}
>
  {@render children?.()}
</span>
