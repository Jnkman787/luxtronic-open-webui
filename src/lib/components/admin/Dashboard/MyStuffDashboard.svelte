<script lang="ts">
	/**
	 * My Stuff Dashboard - displays user's saved charts with customizable timeframes.
	 */
	import { onMount, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';

	import ChartRenderer from '$lib/components/common/ChartRenderer.svelte';
	import TimeframeDropdown from './TimeframeDropdown.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	import {
		getSavedItems,
		deleteSavedItem,
		updateSavedItem,
		getMyStuffChartData,
		type SavedItem,
		type ChartData
	} from '$lib/apis/saved-items';

	const i18n = getContext('i18n');

	export let token: string;
	export let isDark: boolean = false;

	// State
	let items: SavedItem[] = [];
	let loading = true;
	let error: string | null = null;

	// Chart data cache: itemId -> chart data
	let chartDataCache: Map<string, ChartData> = new Map();
	let chartLoadingStates: Map<string, boolean> = new Map();
	let chartErrors: Map<string, string> = new Map();

	// Timeframe overrides per chart: itemId -> {type, value}
	let chartTimeframes: Map<string, { type: string; value: number }> = new Map();

	// Edit state
	let editingTitleId: string | null = null;
	let editingTitleValue: string = '';

	onMount(async () => {
		await loadItems();
	});

	async function loadItems() {
		loading = true;
		error = null;

		try {
			items = await getSavedItems(token);
			// Load chart data for all items
			await Promise.all(items.map((item) => loadChartData(item)));
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load saved items';
			console.error('Failed to load saved items:', e);
		} finally {
			loading = false;
		}
	}

	async function loadChartData(item: SavedItem) {
		const itemId = item.id;
		chartLoadingStates.set(itemId, true);
		chartLoadingStates = chartLoadingStates;

		// Get timeframe (use override or original)
		const timeframe = chartTimeframes.get(itemId) || {
			type: item.timeframe_type,
			value: item.timeframe_value
		};

		try {
			const data = await getMyStuffChartData(
				token,
				item.sql_template,
				timeframe.type,
				timeframe.value,
				item.series_config || undefined
			);

			if (data.error) {
				chartErrors.set(itemId, data.error);
				chartErrors = chartErrors;
			} else {
				chartDataCache.set(itemId, data);
				chartDataCache = chartDataCache;
				chartErrors.delete(itemId);
				chartErrors = chartErrors;
			}
		} catch (e) {
			chartErrors.set(itemId, 'Failed to load chart data');
			chartErrors = chartErrors;
			console.error(`Failed to load chart data for ${itemId}:`, e);
		} finally {
			chartLoadingStates.set(itemId, false);
			chartLoadingStates = chartLoadingStates;
		}
	}

	async function handleRefresh(item: SavedItem) {
		await loadChartData(item);
	}

	async function handleTimeframeChange(item: SavedItem, type: string, value: number) {
		chartTimeframes.set(item.id, { type, value });
		chartTimeframes = chartTimeframes;
		await loadChartData(item);
	}

	async function handleDelete(item: SavedItem) {
		if (!confirm('Are you sure you want to delete this chart?')) {
			return;
		}

		try {
			await deleteSavedItem(token, item.id);
			items = items.filter((i) => i.id !== item.id);
			chartDataCache.delete(item.id);
			chartTimeframes.delete(item.id);
			chartErrors.delete(item.id);
			toast.success('Chart deleted');
		} catch (e) {
			toast.error('Failed to delete chart');
			console.error('Failed to delete chart:', e);
		}
	}

	function startEditingTitle(item: SavedItem) {
		editingTitleId = item.id;
		editingTitleValue = item.title;
	}

	async function saveTitle(item: SavedItem) {
		if (editingTitleValue.trim() === '') {
			editingTitleValue = item.title;
			editingTitleId = null;
			return;
		}

		if (editingTitleValue === item.title) {
			editingTitleId = null;
			return;
		}

		try {
			const updated = await updateSavedItem(token, item.id, { title: editingTitleValue });
			const idx = items.findIndex((i) => i.id === item.id);
			if (idx !== -1) {
				items[idx] = updated;
				items = items;
			}
			toast.success('Title updated');
		} catch (e) {
			toast.error('Failed to update title');
			console.error('Failed to update title:', e);
		} finally {
			editingTitleId = null;
		}
	}

	function cancelEditingTitle() {
		editingTitleId = null;
		editingTitleValue = '';
	}

	function getChartType(item: SavedItem): 'line' | 'bar' | 'pie' | 'scatter' {
		return (item.type as 'line' | 'bar' | 'pie' | 'scatter') || 'line';
	}

	function getTimeframe(item: SavedItem): { type: 'days' | 'hours'; value: number } {
		const override = chartTimeframes.get(item.id);
		if (override) {
			return {
				type: override.type as 'days' | 'hours',
				value: override.value
			};
		}
		return {
			type: item.timeframe_type as 'days' | 'hours',
			value: item.timeframe_value
		};
	}
</script>

<div class="my-stuff-dashboard p-4">
	<!-- Header -->
	<div class="flex justify-between items-center mb-6">
		<h1 class="text-xl font-semibold {isDark ? 'text-white' : 'text-gray-900'}">My Stuff</h1>
		{#if !loading && items.length > 0}
			<span class="text-sm {isDark ? 'text-gray-400' : 'text-gray-500'}">
				{items.length} saved chart{items.length === 1 ? '' : 's'}
			</span>
		{/if}
	</div>

	<!-- Loading state -->
	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#5CC9D3]"></div>
		</div>
	{:else if error}
		<!-- Error state -->
		<div class="text-center py-12">
			<p class="text-red-500">{error}</p>
			<button
				class="mt-4 px-4 py-2 text-sm font-medium rounded-lg bg-[#5CC9D3] text-white hover:bg-[#4bb9c3] transition"
				on:click={loadItems}
			>
				Try Again
			</button>
		</div>
	{:else if items.length === 0}
		<!-- Empty state -->
		<div class="text-center py-12">
			<svg
				class="mx-auto h-12 w-12 {isDark ? 'text-gray-600' : 'text-gray-400'}"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="1.5"
					d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
				/>
			</svg>
			<h3 class="mt-4 text-sm font-medium {isDark ? 'text-white' : 'text-gray-900'}">No saved charts</h3>
			<p class="mt-2 text-sm {isDark ? 'text-gray-400' : 'text-gray-500'}">
				Save charts from your conversations to see them here.
			</p>
		</div>
	{:else}
		<!-- Chart grid -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
			{#each items as item (item.id)}
				{@const chartData = chartDataCache.get(item.id)}
				{@const isLoading = chartLoadingStates.get(item.id)}
				{@const chartError = chartErrors.get(item.id)}
				{@const timeframe = getTimeframe(item)}

				<div
					class="chart-card rounded-lg border transition-shadow hover:shadow-md
						{isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}"
				>
					<!-- Card header -->
					<div
						class="flex items-center justify-between p-3 border-b
							{isDark ? 'border-gray-700' : 'border-gray-100'}"
					>
						<!-- Title (editable) -->
						<div class="flex-1 min-w-0 mr-2">
							{#if editingTitleId === item.id}
								<input
									type="text"
									bind:value={editingTitleValue}
									class="w-full text-sm font-medium px-2 py-1 rounded border
										{isDark
										? 'bg-gray-700 border-gray-600 text-white'
										: 'bg-white border-gray-300 text-gray-900'}
										focus:outline-none focus:ring-1 focus:ring-[#5CC9D3]"
									on:blur={() => saveTitle(item)}
									on:keydown={(e) => {
										if (e.key === 'Enter') saveTitle(item);
										if (e.key === 'Escape') cancelEditingTitle();
									}}
									autofocus
								/>
							{:else}
								<button
									class="w-full text-left text-sm font-medium truncate
										{isDark ? 'text-white' : 'text-gray-900'}
										hover:underline cursor-pointer"
									title="Click to edit title"
									on:click={() => startEditingTitle(item)}
								>
									{item.title}
								</button>
							{/if}
						</div>

						<!-- Actions -->
						<div class="flex items-center gap-2">
							<!-- Timeframe dropdown -->
							<TimeframeDropdown
								type={timeframe.type}
								value={timeframe.value}
								{isDark}
								disabled={isLoading}
								on:change={(e) => handleTimeframeChange(item, e.detail.type, e.detail.value)}
							/>

							<!-- Refresh button -->
							<Tooltip content="Refresh" placement="bottom">
								<button
									class="p-1.5 rounded transition-colors
										{isDark
										? 'hover:bg-gray-700 text-gray-400 hover:text-white'
										: 'hover:bg-gray-100 text-gray-500 hover:text-gray-700'}
										{isLoading ? 'animate-spin' : ''}"
									disabled={isLoading}
									on:click={() => handleRefresh(item)}
								>
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
											d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
										/>
									</svg>
								</button>
							</Tooltip>

							<!-- Delete button -->
							<Tooltip content="Delete" placement="bottom">
								<button
									class="p-1.5 rounded transition-colors
										{isDark
										? 'hover:bg-red-900/50 text-gray-400 hover:text-red-400'
										: 'hover:bg-red-50 text-gray-500 hover:text-red-600'}"
									on:click={() => handleDelete(item)}
								>
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
											d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"
										/>
									</svg>
								</button>
							</Tooltip>
						</div>
					</div>

					<!-- Card body - chart -->
					<div class="p-3 min-h-[250px]">
						{#if isLoading}
							<div class="flex items-center justify-center h-[200px]">
								<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
							</div>
						{:else if chartError}
							<div class="flex flex-col items-center justify-center h-[200px] text-center">
								<svg
									class="h-8 w-8 {isDark ? 'text-red-400' : 'text-red-500'} mb-2"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
									/>
								</svg>
								<p class="text-sm {isDark ? 'text-gray-400' : 'text-gray-500'}">
									Unable to load chart data
								</p>
								<button
									class="mt-2 text-xs text-[#5CC9D3] hover:underline"
									on:click={() => handleRefresh(item)}
								>
									Try again
								</button>
							</div>
						{:else if chartData}
							<ChartRenderer
								chartData={{
									type: getChartType(item),
									title: '',
									labels: chartData.labels,
									series: chartData.series
								}}
								{isDark}
								height={220}
								showLegend={true}
								showGrid={true}
							/>
						{:else}
							<div class="flex items-center justify-center h-[200px]">
								<p class="text-sm {isDark ? 'text-gray-500' : 'text-gray-400'}">No data</p>
							</div>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
