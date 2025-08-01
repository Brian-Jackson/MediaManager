<script lang="ts">
	import { getFullyQualifiedMediaName, getTorrentQualityString } from '$lib/utils.js';
	import type { MovieRequest, SeasonRequest, User } from '$lib/types.js';
	import CheckmarkX from '$lib/components/checkmark-x.svelte';
	import * as Table from '$lib/components/ui/table/index.js';
	import { getContext } from 'svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { env } from '$env/dynamic/public';
	import { toast } from 'svelte-sonner';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';

	const apiUrl = env.PUBLIC_API_URL;
	let {
		requests,
		filter = () => true,
		isShow = true
	}: {
		requests: (SeasonRequest | MovieRequest)[];
		filter?: (request: SeasonRequest | MovieRequest) => boolean;
		isShow: boolean;
	} = $props();
	const user: () => User = getContext('user');

	async function approveRequest(requestId: string, currentAuthorizedStatus: boolean) {
		try {
			const response = await fetch(
				`${apiUrl}${isShow ? '/tv/seasons' : '/movies'}/requests/${requestId}?authorized_status=${!currentAuthorizedStatus}`,
				{
					method: 'PATCH',
					headers: {
						'Content-Type': 'application/json'
					},
					credentials: 'include'
				}
			);

			if (response.ok) {
				const requestIndex = requests.findIndex((r) => r.id === requestId);
				if (requestIndex !== -1) {
					let newAuthorizedStatus = !currentAuthorizedStatus;
					requests[requestIndex].authorized = newAuthorizedStatus;
					requests[requestIndex].authorized_by = newAuthorizedStatus ? user() : undefined;
				}
				toast.success(
					`Request ${!currentAuthorizedStatus ? 'approved' : 'unapproved'} successfully.`
				);
			} else {
				const errorText = await response.text();
				console.error(`Failed to update request status ${response.statusText}`, errorText);
				toast.error(`Failed to update request status: ${response.statusText}`);
			}
		} catch (error) {
			console.error('Error updating request status:', error);
			toast.error(
				'Error updating request status: ' + (error instanceof Error ? error.message : String(error))
			);
		}
	}

	async function deleteRequest(requestId: string) {
		try {
			const response = await fetch(
				`${apiUrl}${isShow ? '/tv/seasons' : '/movies'}/requests/${requestId}`,
				{
					method: 'DELETE',
					headers: {
						'Content-Type': 'application/json'
					},
					credentials: 'include'
				}
			);

			if (response.ok) {
				const index = requests.findIndex((r) => r.id === requestId);
				if (index > -1) {
					requests.splice(index, 1); // Remove the request from the list
				}
				toast.success('Request deleted successfully');
			} else {
				console.error(`Failed to delete request ${response.statusText}`, await response.text());
				toast.error('Failed to delete request');
			}
		} catch (error) {
			console.error('Error deleting request:', error);
			toast.error(
				'Error deleting request: ' + (error instanceof Error ? error.message : String(error))
			);
		}
	}
</script>

<Table.Root>
	<Table.Caption>A list of all requests.</Table.Caption>
	<Table.Header>
		<Table.Row>
			<Table.Head>{isShow ? 'Show' : 'Movie'}</Table.Head>
			{#if isShow}
				<Table.Head>Season</Table.Head>
			{/if}
			<Table.Head>Minimum Quality</Table.Head>
			<Table.Head>Wanted Quality</Table.Head>
			<Table.Head>Requested by</Table.Head>
			<Table.Head>Approved</Table.Head>
			<Table.Head>Approved by</Table.Head>
			<Table.Head>Actions</Table.Head>
		</Table.Row>
	</Table.Header>
	<Table.Body>
		{#each requests as request (request.id)}
			{#if filter(request)}
				<Table.Row>
					<Table.Cell>
						{#if isShow}
							{getFullyQualifiedMediaName((request as SeasonRequest).show)}
						{:else}
							{getFullyQualifiedMediaName((request as MovieRequest).movie)}
						{/if}
					</Table.Cell>
					{#if isShow}
						<Table.Cell>
							{(request as SeasonRequest).season.number}
						</Table.Cell>
					{/if}
					<Table.Cell>
						{getTorrentQualityString(request.min_quality)}
					</Table.Cell>
					<Table.Cell>
						{getTorrentQualityString(request.wanted_quality)}
					</Table.Cell>
					<Table.Cell>
						{request.requested_by?.email ?? 'N/A'}
					</Table.Cell>
					<Table.Cell>
						<CheckmarkX state={request.authorized} />
					</Table.Cell>
					<Table.Cell>
						{request.authorized_by?.email ?? 'N/A'}
					</Table.Cell>
					<!-- TODO: ADD DIALOGUE TO MODIFY REQUEST -->
					<Table.Cell class="flex max-w-[150px] flex-col gap-1">
						{#if user().is_superuser}
							<Button
								class=""
								size="sm"
								onclick={() => approveRequest(request.id, request.authorized)}
							>
								{request.authorized ? 'Unapprove' : 'Approve'}
							</Button>
							{#if isShow}
								<Button
									class=""
									size="sm"
									variant="outline"
									onclick={() => goto(base + '/dashboard/tv/' + (request as SeasonRequest).show.id)}
								>
									Download manually
								</Button>
							{:else}
								<Button
									class=""
									size="sm"
									variant="outline"
									onclick={() =>
										goto(base + '/dashboard/movies/' + (request as MovieRequest).movie.id)}
								>
									Download manually
								</Button>
							{/if}
						{/if}
						{#if user().is_superuser || user().id === request.requested_by?.id}
							<Button variant="destructive" size="sm" onclick={() => deleteRequest(request.id)}
								>Delete
							</Button>
						{/if}
					</Table.Cell>
				</Table.Row>
			{/if}
		{:else}
			<Table.Row>
				<Table.Cell colspan={8} class="text-center">There are currently no requests.</Table.Cell>
			</Table.Row>
		{/each}
	</Table.Body>
</Table.Root>
