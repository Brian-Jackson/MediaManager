<script lang="ts">
	import { Menubar as MenubarPrimitive } from 'bits-ui';
	import { cn } from '$lib/utils.js';

	let {
		ref = $bindable(null),
		class: className,
		inset,
		...restProps
	}: MenubarPrimitive.ItemProps & {
		inset?: boolean;
	} = $props();
</script>

<MenubarPrimitive.Item
	{...restProps}
	bind:ref
	class={cn(
		'relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none data-[disabled]:pointer-events-none data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground data-[disabled]:opacity-50',
		inset && 'pl-8',
		className
	)}
/>
