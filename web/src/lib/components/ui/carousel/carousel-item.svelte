<script lang="ts">
	import type { WithElementRef } from 'bits-ui';
	import type { HTMLAttributes } from 'svelte/elements';
	import { getEmblaContext } from './context.js';
	import { cn } from '$lib/utils.js';

	let {
		ref = $bindable(null),
		class: className,
		children,
		...restProps
	}: WithElementRef<HTMLAttributes<HTMLDivElement>> = $props();

	const emblaCtx = getEmblaContext('<Carousel.Item/>');
</script>

<div
	{...restProps}
	aria-roledescription="slide"
	bind:this={ref}
	class={cn(
		'min-w-0 shrink-0 grow-0 basis-full',
		emblaCtx.orientation === 'horizontal' ? 'pl-4' : 'pt-4',
		className
	)}
	data-embla-slide=""
	role="group"
>
	{@render children?.()}
</div>
