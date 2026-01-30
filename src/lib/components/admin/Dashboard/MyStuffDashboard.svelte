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
		reorderSavedItems,
		getMyStuffChartData,
		type SavedItem,
		type ChartData,
		type SeriesConfig
	} from '$lib/apis/saved-items';
	import { dndzone } from 'svelte-dnd-action';

	const i18n = getContext('i18n');

	export let token: string;
	export let isDark: boolean = false;

	// State
	let items: SavedItem[] = [];
	let lastCommittedItems: SavedItem[] = [];
	let loading = true;
	let error: string | null = null;

	// Chart data cache: itemId -> chart data (using objects for Svelte reactivity)
	let chartDataCache: Record<string, ChartData> = {};
	let chartLoadingStates: Record<string, boolean> = {};
	let chartErrors: Record<string, string> = {};

	// Timeframe overrides per chart: itemId -> {type, value}
	let chartTimeframes: Record<string, { type: string; value: number }> = {};

	// Edit state
	let editingTitleId: string | null = null;
	let editingTitleValue: string = '';

	// Series config edit state
	let editingSeriesId: string | null = null;
	let editingSeriesConfig: SeriesConfig[] = [];

	onMount(async () => {
		await loadItems();
	});

	async function loadItems() {
		loading = true;
		error = null;

		try {
			items = await getSavedItems(token);
			lastCommittedItems = [...items];
			// Load chart data for all items
			await Promise.all(items.map((item) => loadChartData(item)));
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load saved items';
		} finally {
			loading = false;
		}
	}

	async function loadChartData(item: SavedItem) {
		const itemId = item.id;

		chartLoadingStates = { ...chartLoadingStates, [itemId]: true };

		// Get timeframe (use override or original)
		const timeframe = chartTimeframes[itemId] || {
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
				chartErrors = { ...chartErrors, [itemId]: data.error };
			} else {
				chartDataCache = { ...chartDataCache, [itemId]: data };
				const { [itemId]: _, ...restErrors } = chartErrors;
				chartErrors = restErrors;
			}
		} catch (e) {
			chartErrors = { ...chartErrors, [itemId]: 'Failed to load chart data' };
		} finally {
			chartLoadingStates = { ...chartLoadingStates, [itemId]: false };
		}
	}

	async function handleRefresh(item: SavedItem) {
		await loadChartData(item);
	}

	async function handleTimeframeChange(item: SavedItem, type: string, value: number) {
		chartTimeframes = { ...chartTimeframes, [item.id]: { type, value } };
		await loadChartData(item);
	}

	async function handleDelete(item: SavedItem) {
		if (!confirm('Are you sure you want to delete this chart?')) {
			return;
		}

		try {
			await deleteSavedItem(token, item.id);
			items = items.filter((i) => i.id !== item.id);
			lastCommittedItems = [...items];
			const { [item.id]: _cache, ...restCache } = chartDataCache;
			chartDataCache = restCache;
			const { [item.id]: _timeframe, ...restTimeframes } = chartTimeframes;
			chartTimeframes = restTimeframes;
			const { [item.id]: _error, ...restErrors } = chartErrors;
			chartErrors = restErrors;
			toast.success('Chart deleted');
		} catch (e) {
			toast.error('Failed to delete chart');
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
		} finally {
			editingTitleId = null;
		}
	}

	function cancelEditingTitle() {
		editingTitleId = null;
		editingTitleValue = '';
	}

	function startEditingSeries(item: SavedItem) {
		// Initialize from saved config or chart data
		const chartData = chartDataCache[item.id];

		if (item.series_config && item.series_config.length > 0) {
			// Use saved config, ensure column field exists
			editingSeriesConfig = item.series_config.map((s, i) => ({
				column: s.column || s.name,  // Fallback for old configs without column
				name: s.name,
				color: s.color || chartData?.series?.[i]?.color || '#5CC9D3'
			}));
		} else if (chartData?.series) {
			// Initialize from chart data (first time editing)
			editingSeriesConfig = chartData.series.map((s) => ({
				column: s.name,  // Original column name
				name: s.name,    // Display name (starts same as column)
				color: s.color
			}));
		} else {
			editingSeriesConfig = [];
		}
		editingSeriesId = item.id;
	}

	async function saveSeriesConfig(item: SavedItem) {
		if (editingSeriesConfig.length === 0) {
			editingSeriesId = null;
			return;
		}

		try {
			const updated = await updateSavedItem(token, item.id, { series_config: editingSeriesConfig });
			const idx = items.findIndex((i) => i.id === item.id);
			if (idx !== -1) {
				items[idx] = updated;
				items = items;
			}
			toast.success('Series names updated');
			// Reload chart data to reflect new names
			await loadChartData(updated);
		} catch (e) {
			toast.error('Failed to update series names');
		} finally {
			editingSeriesId = null;
			editingSeriesConfig = [];
		}
	}

	function cancelEditingSeries() {
		editingSeriesId = null;
		editingSeriesConfig = [];
	}

	function updateSeriesName(index: number, name: string) {
		editingSeriesConfig = editingSeriesConfig.map((s, i) =>
			i === index ? { ...s, name } : s
		);
	}

	function getChartType(item: SavedItem): 'line' | 'bar' | 'pie' | 'scatter' {
		return (item.type as 'line' | 'bar' | 'pie' | 'scatter') || 'line';
	}

	function getTimeframe(item: SavedItem): { type: 'days' | 'hours'; value: number } {
		const override = chartTimeframes[item.id];
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

	function handleDndConsider(event: CustomEvent<{ items: SavedItem[] }>) {
		items = event.detail.items;
	}

	async function handleDndFinalize(event: CustomEvent<{ items: SavedItem[] }>) {
		const newItems = event.detail.items;
		items = newItems;

		try {
			await reorderSavedItems(
				token,
				newItems.map((item) => item.id)
			);
			lastCommittedItems = [...newItems];
		} catch (e) {
			items = [...lastCommittedItems];
			toast.error('Failed to reorder charts');
		}
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
		<div
			class="grid grid-cols-1 lg:grid-cols-2 gap-4"
			use:dndzone={{ items, flipDurationMs: 150 }}
			on:consider={handleDndConsider}
			on:finalize={handleDndFinalize}
		>
			{#each items as item (item.id)}
				<div
					class="chart-card rounded-lg border transition-shadow hover:shadow-md cursor-move
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
								type={getTimeframe(item).type}
								value={getTimeframe(item).value}
								{isDark}
								disabled={chartLoadingStates[item.id]}
								on:change={(e) => handleTimeframeChange(item, e.detail.type, e.detail.value)}
							/>

							<!-- Edit series names button -->
							<Tooltip content="Edit series names" placement="bottom">
								<button
									class="p-1.5 rounded transition-colors
										{isDark
										? 'hover:bg-gray-700 text-gray-400 hover:text-white'
										: 'hover:bg-gray-100 text-gray-500 hover:text-gray-700'}
										{editingSeriesId === item.id ? 'bg-[#5CC9D3]/20 text-[#5CC9D3]' : ''}"
									disabled={chartLoadingStates[item.id] || !chartDataCache[item.id]?.series?.length}
									on:click={() => editingSeriesId === item.id ? cancelEditingSeries() : startEditingSeries(item)}
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
											d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z"
										/>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
										/>
									</svg>
								</button>
							</Tooltip>

							<!-- Refresh button -->
							<Tooltip content="Refresh" placement="bottom">
								<button
									class="p-1.5 rounded transition-colors
										{isDark
										? 'hover:bg-gray-700 text-gray-400 hover:text-white'
										: 'hover:bg-gray-100 text-gray-500 hover:text-gray-700'}
										{chartLoadingStates[item.id] ? 'animate-spin' : ''}"
									disabled={chartLoadingStates[item.id]}
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

					<!-- Series config editor -->
					{#if editingSeriesId === item.id}
						<div
							class="p-3 border-b {isDark ? 'border-gray-700 bg-gray-800/50' : 'border-gray-100 bg-gray-50'}"
						>
							<div class="text-xs font-medium mb-2 {isDark ? 'text-gray-400' : 'text-gray-500'}">
								Edit Series Names
							</div>
							<div class="space-y-2">
								{#each editingSeriesConfig as series, index}
									<div class="flex items-center gap-2">
										<div
											class="w-3 h-3 rounded-full flex-shrink-0"
											style="background-color: {series.color}"
										></div>
										<input
											type="text"
											value={series.name}
											on:input={(e) => updateSeriesName(index, e.currentTarget.value)}
											class="flex-1 text-sm px-2 py-1 rounded border
												{isDark
												? 'bg-gray-700 border-gray-600 text-white'
												: 'bg-white border-gray-300 text-gray-900'}
												focus:outline-none focus:ring-1 focus:ring-[#5CC9D3]"
											placeholder="Series name"
										/>
									</div>
								{/each}
							</div>
							<div class="flex justify-end gap-2 mt-3">
								<button
									class="px-3 py-1 text-xs font-medium rounded
										{isDark
										? 'text-gray-400 hover:text-white hover:bg-gray-700'
										: 'text-gray-600 hover:text-gray-900 hover:bg-gray-200'}"
									on:click={cancelEditingSeries}
								>
									Cancel
								</button>
								<button
									class="px-3 py-1 text-xs font-medium rounded bg-[#5CC9D3] text-white hover:bg-[#4bb9c3]"
									on:click={() => saveSeriesConfig(item)}
								>
									Save
								</button>
							</div>
						</div>
					{/if}

					<!-- Card body - chart -->
					<div class="p-3 min-h-[250px] overflow-hidden">
						{#if chartLoadingStates[item.id]}
							<div class="flex items-center justify-center h-[200px]">
								<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
							</div>
						{:else if chartErrors[item.id]}
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
						{:else if chartDataCache[item.id]}
							<ChartRenderer
								chartData={{
									type: getChartType(item),
									title: '',
									labels: chartDataCache[item.id].labels,
									series: chartDataCache[item.id].series
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
