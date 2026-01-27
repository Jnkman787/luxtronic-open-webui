<script lang="ts">
	/**
	 * "Add to My Stuff" button for saving charts from chat to the My Stuff dashboard.
	 */
	import { createEventDispatcher, getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';

	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import { checkMessageSaved, createSavedItem } from '$lib/apis/saved-items';

	const i18n = getContext<Writable<i18nType>>('i18n');
	const dispatch = createEventDispatcher();

	export let messageId: string;
	export let chatId: string = '';
	export let chartData: {
		type: string;
		title: string;
		labels: string[];
		series: Array<{ name: string; values: number[]; color: string }>;
		timeframe?: { type: string; value: number };
		sql_template?: string;
	} | null = null;
	export let isVisible: boolean = true;

	let token = '';
	let isSaved = false;
	let isSaving = false;
	let checkingStatus = true;

	onMount(async () => {
		token = localStorage.getItem('token') || '';
		if (token && messageId) {
			try {
				isSaved = await checkMessageSaved(token, messageId);
			} catch (e) {
				console.error('Failed to check if message is saved:', e);
			}
		}
		checkingStatus = false;
	});

	async function handleSave() {
		if (!chartData || !token || isSaving || isSaved) return;

		isSaving = true;

		try {
			await createSavedItem(token, {
				chat_id: chatId || undefined,
				message_id: messageId,
				type: chartData.type || 'line',
				title: chartData.title || 'Saved Chart',
				sql_template: chartData.sql_template || '',
				series_config: chartData.series?.map((s) => ({ name: s.name, color: s.color })),
				timeframe_type: chartData.timeframe?.type || 'days',
				timeframe_value: chartData.timeframe?.value || 7
			});

			isSaved = true;
			toast.success($i18n.t('Chart saved to My Stuff'));
			dispatch('saved');
		} catch (e) {
			const errorMessage = e instanceof Error ? e.message : 'Failed to save chart';
			if (errorMessage.includes('already')) {
				isSaved = true;
			} else {
				toast.error(errorMessage);
			}
			console.error('Failed to save chart:', e);
		} finally {
			isSaving = false;
		}
	}
</script>

{#if chartData && isVisible && !checkingStatus}
	{#if !isSaved}
		<Tooltip content={$i18n.t('Add to My Stuff')} placement="bottom">
			<button
				aria-label={$i18n.t('Add to My Stuff')}
				class="p-1.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-lg dark:hover:text-white hover:text-black transition"
				disabled={isSaving}
				on:click={handleSave}
			>
				{#if isSaving}
					<svg
						class="w-4 h-4 animate-spin"
						fill="none"
						viewBox="0 0 24 24"
						xmlns="http://www.w3.org/2000/svg"
					>
						<circle
							class="opacity-25"
							cx="12"
							cy="12"
							r="10"
							stroke="currentColor"
							stroke-width="4"
						/>
						<path
							class="opacity-75"
							fill="currentColor"
							d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						/>
					</svg>
				{:else}
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="2"
						stroke="currentColor"
						class="w-4 h-4"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z"
						/>
					</svg>
				{/if}
			</button>
		</Tooltip>
	{:else}
		<Tooltip content={$i18n.t('Saved to My Stuff')} placement="bottom">
			<span class="p-1.5 text-[#5CC9D3]">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 24 24"
					fill="currentColor"
					class="w-4 h-4"
				>
					<path
						fill-rule="evenodd"
						d="M6.32 2.577a49.255 49.255 0 0111.36 0c1.497.174 2.57 1.46 2.57 2.93V21a.75.75 0 01-1.085.67L12 18.089l-7.165 3.583A.75.75 0 013.75 21V5.507c0-1.47 1.073-2.756 2.57-2.93z"
						clip-rule="evenodd"
					/>
				</svg>
			</span>
		</Tooltip>
	{/if}
{/if}
