<script lang="ts">
	/**
	 * "Add to My Stuff" button for saving charts from chat to the My Stuff dashboard.
	 * Styled to match the Export to Excel button.
	 */
	import { createEventDispatcher, getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';

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
	export let visibilityClass: string = 'visible';

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
				series_config: chartData.series?.map((s) => ({ column: s.name, name: s.name, color: s.color })),
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

{#if chartData && !checkingStatus}
	{#if !isSaved}
		<button
			aria-label={$i18n.t('Add to My Stuff')}
			class="{visibilityClass} px-2.5 py-1.5 text-xs font-medium border border-gray-700 dark:border-gray-200 rounded-lg text-gray-700 dark:text-gray-200 hover:bg-gray-900 hover:text-white dark:hover:bg-gray-100 dark:hover:text-gray-900 transition disabled:opacity-50 disabled:cursor-not-allowed"
			disabled={isSaving}
			on:click={handleSave}
		>
			{#if isSaving}
				{$i18n.t('Saving...')}
			{:else}
				{$i18n.t('Add to My Stuff')}
			{/if}
		</button>
	{:else}
		<span
			class="{visibilityClass} px-2.5 py-1.5 text-xs font-medium border border-[#5CC9D3] rounded-lg text-[#5CC9D3] cursor-default"
		>
			{$i18n.t('Saved to My Stuff')}
		</span>
	{/if}
{/if}
