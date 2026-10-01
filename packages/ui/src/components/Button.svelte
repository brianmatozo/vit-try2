<script lang="ts">
import type { Snippet } from 'svelte';
import type { HTMLButtonAttributes } from 'svelte/elements';
import { cn } from '../utils.js';

interface Props extends HTMLButtonAttributes {
	variant?: 'primary' | 'secondary' | 'outline' | 'destructive' | 'ghost';
	size?: 'sm' | 'md' | 'lg';
	children?: Snippet;
}

let {
	variant = 'primary',
	size = 'md',
	class: className = '',
	children,
	...restProps
}: Props = $props();

const variantClasses = {
	primary:
		'bg-emerald-600 text-white hover:bg-emerald-700 active:bg-emerald-800 shadow-sm',
	secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200 active:bg-gray-300',
	outline:
		'border border-gray-300 text-gray-700 hover:bg-gray-50 active:bg-gray-100',
	destructive:
		'bg-rose-600 text-white hover:bg-rose-700 active:bg-rose-800 shadow-sm',
	ghost: 'text-gray-700 hover:bg-gray-100 active:bg-gray-200',
};

const sizeClasses = {
	sm: 'px-2.5 py-1.5 text-xs rounded font-medium',
	md: 'px-4 py-2 text-sm rounded-md font-medium',
	lg: 'px-6 py-3 text-base rounded-lg font-semibold',
};
</script>

<button
  class={cn(
    'inline-flex items-center justify-center transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 disabled:opacity-50 disabled:pointer-events-none cursor-pointer select-none',
    variantClasses[variant],
    sizeClasses[size],
    className
  )}
  {...restProps}
>
  {@render children?.()}
</button>
