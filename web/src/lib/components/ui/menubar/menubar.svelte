<script lang="ts">
	import { Menubar as MenubarPrimitive } from 'bits-ui';
	import { cn } from '$lib/utils.js';

	let {
		ref = $bindable(null),
		class: className,
		...restProps
	}: MenubarPrimitive.RootProps = $props();
</script>

<MenubarPrimitive.Root
	{...restProps}
	bind:ref
	class={cn(
		'flex h-9 items-center space-x-1 rounded-md border bg-background p-1 shadow-sm',
		className
	)}
/>
