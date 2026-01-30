<script lang="ts">
	import { onMount } from 'svelte';
	import ToggleBar from './Toggle/ToggleBar.svelte';
	import DPMOCard from './Cards/DPMOCard.svelte';
	import MetricCard from './Cards/MetricCard.svelte';
	import LineChart from './Charts/LineChart.svelte';
	import MultiLineChart from './Charts/MultiLineChart.svelte';
	import CaseInspectionIncidentsList from './Incidents/CaseInspectionIncidentsList.svelte';
	import {
		getCaseInspectionSnapshot,
		getCaseInspectionThroughput,
		getCaseInspectionDefects,
		getCaseInspectionIncidents,
		getSystemHealth,
		type TenantDashboardConfig,
		type CaseInspectionSnapshotResponse,
		type CaseInspectionThroughputResponse,
		type CaseInspectionDefectsResponse,
		type CaseInspectionIncidentsResponse,
		type DeviceHealth
	} from '$lib/apis/dashboard';
	import { chartColors } from '$lib/stores/dashboard';

	export let token: string;
	export let tenantId: string;
	export let rangeLabel: string;
	export let rangeParams: { days?: number; rangeHours?: number };
	export let isDark: boolean = false;
	export let tenantConfig: TenantDashboardConfig | null = null;

	const DPMO_HELP =
		'Defects per million opportunities: (defects / total cases) x 1,000,000 over the selected time range.';

	const viewOptions = ['Throughput', 'Defects', 'System Health'];
	const defectKeyOrder = [
		{ key: 'down', label: 'Down' },
		{ key: 'empty', label: 'Empty' },
		{ key: 'upside_down', label: 'Upside Down' },
		{ key: 'broken_glass', label: 'Broken Glass' }
	];

	let selectedShop = '';
	let selectedView = viewOptions[0];
	let initialized = false;
	let lastRangeKey = '';
	let currentTenantId = '';

	let snapshot: CaseInspectionSnapshotResponse | null = null;
	let snapshotLoading = false;
	let snapshotError: string | null = null;

	let throughput: CaseInspectionThroughputResponse | null = null;
	let throughputLoading = false;
	let throughputError: string | null = null;

	let defects: CaseInspectionDefectsResponse | null = null;
	let defectsLoading = false;
	let defectsError: string | null = null;

	let incidents: CaseInspectionIncidentsResponse | null = null;
	let incidentsLoading = false;
	let incidentsError: string | null = null;

	let systemHealthAll: DeviceHealth[] = [];
	let systemHealthLoading = false;
	let systemHealthError: string | null = null;
	let systemHealthTimestamp = '';

	$: shopOptions = tenantConfig?.available_lines?.length ? tenantConfig.available_lines : [];
	$: defectTotals = defects?.totals || {};
	$: defectKeys = Object.keys(defectTotals);
	$: defectOrder = defectKeyOrder.filter((item) => defectKeys.includes(item.key));
	$: defectSeries = defects?.series || [];
	$: throughputTrend = throughput?.trend || [];
	$: filteredSystemHealth = systemHealthAll.filter((device) => device.line_id === selectedShop);
	$: rangeDays = rangeParams?.days ?? 7;
	$: rangeHours = rangeParams?.rangeHours;
	$: rangeKey = rangeHours ? `h${rangeHours}` : `d${rangeDays}`;

	$: if (tenantId && tenantId !== currentTenantId && shopOptions.length > 0) {
		currentTenantId = tenantId;
		selectedShop = shopOptions[0];
		selectedView = viewOptions[0];
		if (initialized) {
			loadSnapshot();
			refreshView();
			loadIncidents();
		}
	}

	onMount(async () => {
		initialized = true;
		if (!selectedShop && shopOptions.length > 0) {
			selectedShop = shopOptions[0];
		}
		await loadSnapshot();
		await refreshView();
		await loadIncidents();
	});

	$: if (initialized && rangeKey !== lastRangeKey) {
		lastRangeKey = rangeKey;
		loadSnapshot();
		refreshView();
		loadIncidents();
	}

	async function loadSnapshot() {
		snapshotLoading = true;
		snapshotError = null;
		try {
			snapshot = await getCaseInspectionSnapshot(token, tenantId, rangeDays, rangeHours);
		} catch (e) {
			snapshotError = e instanceof Error ? e.message : 'Failed to load snapshot';
		} finally {
			snapshotLoading = false;
		}
	}

	async function loadThroughput() {
		if (!selectedShop) return;
		throughputLoading = true;
		throughputError = null;
		try {
			throughput = await getCaseInspectionThroughput(token, tenantId, selectedShop, rangeDays, rangeHours);
		} catch (e) {
			throughputError = e instanceof Error ? e.message : 'Failed to load throughput';
		} finally {
			throughputLoading = false;
		}
	}

	async function loadDefects() {
		if (!selectedShop) return;
		defectsLoading = true;
		defectsError = null;
		try {
			defects = await getCaseInspectionDefects(token, tenantId, selectedShop, rangeDays, rangeHours);
		} catch (e) {
			defectsError = e instanceof Error ? e.message : 'Failed to load defects';
		} finally {
			defectsLoading = false;
		}
	}

	async function loadIncidents() {
		if (!selectedShop) return;
		incidentsLoading = true;
		incidentsError = null;
		try {
			incidents = await getCaseInspectionIncidents(token, tenantId, selectedShop, rangeDays, 10, rangeHours);
		} catch (e) {
			incidentsError = e instanceof Error ? e.message : 'Failed to load incidents';
		} finally {
			incidentsLoading = false;
		}
	}

	async function loadSystemHealth() {
		systemHealthLoading = true;
		systemHealthError = null;
		try {
			const response = await getSystemHealth(token, tenantId, 30);
			systemHealthAll = response.devices;
			systemHealthTimestamp = response.timestamp;
		} catch (e) {
			systemHealthError = e instanceof Error ? e.message : 'Failed to load system health';
		} finally {
			systemHealthLoading = false;
		}
	}

	async function refreshView() {
		if (!initialized) return;
		if (!selectedShop) return;
		if (selectedView === 'Throughput') {
			await loadThroughput();
		} else if (selectedView === 'Defects') {
			await loadDefects();
		} else {
			await loadSystemHealth();
		}
	}

	function handleShopChange(shop: string) {
		selectedShop = shop;
		refreshView();
		loadIncidents();
	}

	function handleViewChange(view: string) {
		selectedView = view;
		refreshView();
	}
</script>

<div class="space-y-6">
	<div class="space-y-3">
		<h2 class="text-lg font-semibold {isDark ? 'text-white' : 'text-gray-900'}">Quality Snapshot</h2>
		{#if snapshotLoading}
			<div class="flex items-center justify-center h-24">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
			</div>
		{:else if snapshotError}
			<div class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
				{snapshotError}
			</div>
		{:else}
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
				{#each snapshot?.shops || [] as shop}
					<DPMOCard
						line={shop.shop_id}
						dpmo={shop.dpmo}
						totalUnits={shop.total_cases}
						dpmoHelpText={DPMO_HELP}
						{isDark}
					/>
				{/each}
			</div>
		{/if}
	</div>

	<div class="space-y-3">
		<h3 class="text-lg font-semibold {isDark ? 'text-white' : 'text-gray-900'}">Line Metrics</h3>
		<ToggleBar options={shopOptions} selected={selectedShop} onSelect={handleShopChange} {isDark} />
		<ToggleBar options={viewOptions} selected={selectedView} onSelect={handleViewChange} {isDark} size="sm" />
	</div>

	{#if selectedView === 'Throughput'}
		{#if throughputLoading}
			<div class="flex items-center justify-center h-20">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
			</div>
		{:else if throughputError}
			<div class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
				{throughputError}
			</div>
		{:else if throughput}
			<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
				<MetricCard label="Total Cases" value={throughput.total_cases} {isDark} />
			</div>
		{/if}

		<div class="p-4 rounded-lg border {isDark ? 'bg-gray-800/50 border-gray-700/50' : 'bg-white border-gray-200'}">
			<LineChart
				title="Production Trend"
				subtitle={rangeLabel}
				data={throughputTrend}
				color={chartColors.primary}
				{isDark}
				height={250}
			/>
		</div>
	{:else if selectedView === 'Defects'}
		{#if defectsLoading}
			<div class="flex items-center justify-center h-20">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
			</div>
		{:else if defectsError}
			<div class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
				{defectsError}
			</div>
		{:else if defects}
			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
				{#each defectOrder as def}
					<MetricCard label={def.label} value={defectTotals[def.key] ?? 0} {isDark} />
				{/each}
			</div>
		{/if}

		<div class="p-4 rounded-lg border {isDark ? 'bg-gray-800/50 border-gray-700/50' : 'bg-white border-gray-200'}">
			<MultiLineChart
				title="Defect Trend"
				subtitle={rangeLabel}
				series={defectSeries.map((series, index) => ({
					label: series.label,
					color: [chartColors.line1, chartColors.line2, chartColors.line3, chartColors.line4][index % 4],
					data: series.data
				}))}
				{isDark}
				height={250}
			/>
		</div>
	{:else}
		<div class="space-y-4">
			{#if systemHealthLoading}
				<div class="flex items-center justify-center h-32">
					<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
				</div>
			{:else if systemHealthError}
				<div class="p-4 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
					{systemHealthError}
				</div>
			{:else if filteredSystemHealth.length === 0}
				<div class="p-8 text-center {isDark ? 'text-gray-400' : 'text-gray-500'}">
					<p class="text-sm">No device health data available</p>
				</div>
			{:else}
				<div class="flex items-center justify-between mb-2">
					<h4 class="text-sm font-medium {isDark ? 'text-white' : 'text-gray-900'}">
						Device Status
					</h4>
					{#if systemHealthTimestamp}
						<span class="text-xs {isDark ? 'text-gray-500' : 'text-gray-400'}">
							Updated: {new Date(systemHealthTimestamp).toLocaleTimeString()}
						</span>
					{/if}
				</div>
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
					{#each filteredSystemHealth as device}
						<div
							class="p-3 rounded-lg border {isDark
								? 'bg-gray-800/50 border-gray-700/50'
								: 'bg-white border-gray-200'}"
						>
							<div class="flex items-center justify-between mb-2">
								<span class="text-sm font-medium {isDark ? 'text-white' : 'text-gray-900'}">
									{device.line_id}
								</span>
								<span
									class="px-2 py-0.5 rounded-full text-xs font-medium {device.status === 'ok'
										? 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300'
										: device.status === 'warning'
											? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300'
											: device.status === 'error'
												? 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300'
												: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'}"
								>
									{device.status.toUpperCase()}
								</span>
							</div>
							<div class="space-y-1 text-xs {isDark ? 'text-gray-400' : 'text-gray-500'}">
								<div class="flex justify-between">
									<span>System:</span>
									<span class="{isDark ? 'text-gray-300' : 'text-gray-700'}">{device.system.toUpperCase()}</span>
								</div>
								{#if device.latest_fps !== null}
									<div class="flex justify-between">
										<span>FPS:</span>
										<span class="{isDark ? 'text-gray-300' : 'text-gray-700'}">{device.latest_fps.toFixed(1)}</span>
									</div>
								{/if}
								{#if device.last_seen}
									<div class="flex justify-between">
										<span>Last Seen:</span>
										<span class="{isDark ? 'text-gray-300' : 'text-gray-700'}">
											{new Date(device.last_seen).toLocaleTimeString()}
										</span>
									</div>
								{/if}
								{#if device.message}
									<p class="mt-1 text-xs italic {device.status === 'error' ? 'text-red-400' : device.status === 'warning' ? 'text-yellow-400' : ''}">
										{device.message}
									</p>
								{/if}
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	{/if}

	<div class="space-y-3">
		<h3 class="text-sm font-semibold {isDark ? 'text-white' : 'text-gray-900'}">
			Recent Incidents ({rangeLabel})
		</h3>
		<CaseInspectionIncidentsList
			incidents={incidents?.incidents || []}
			{isDark}
			loading={incidentsLoading}
			error={incidentsError}
		/>
	</div>
</div>
