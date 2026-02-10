<script lang="ts">
	import { onMount } from 'svelte';
	import ToggleBar from './Toggle/ToggleBar.svelte';
	import MetricCard from './Cards/MetricCard.svelte';
	import MultiLineChart from './Charts/MultiLineChart.svelte';
	import ScaleWeightBinImagesList from './Incidents/ScaleWeightBinImagesList.svelte';
	import {
		getScaleSnapshot,
		getScaleOverview,
		getScaleBayMetrics,
		getScaleBayTable,
		getScaleBinImages,
		getScaleCameraHealth,
		type TenantDashboardConfig,
		type ScaleSnapshotResponse,
		type ScaleOverviewResponse,
		type ScaleBayMetricsResponse,
		type ScaleBayTableResponse,
		type ScaleBinImagesResponse,
		type ScaleCameraHealthResponse
	} from '$lib/apis/dashboard';
	import { chartColors } from '$lib/stores/dashboard';

	export let token: string;
	export let tenantId: string;
	export let rangeLabel: string;
	export let rangeParams: { days?: number; rangeHours?: number };
	export let isDark: boolean = false;
	export let tenantConfig: TenantDashboardConfig | null = null;

	const viewOptions = ['Overview', 'Bay 1', 'Bay 2', 'Camera Health'];
	const unitOptions = ['Pounds', 'Tons'];

	let selectedSystem = '';
	let selectedView = viewOptions[0];
	let weightUnit = unitOptions[0];
	let currentTenantId = '';
	let initialized = false;
	let lastRangeKey = '';

	let snapshot: ScaleSnapshotResponse | null = null;
	let snapshotLoading = false;
	let snapshotError: string | null = null;

	let overview: ScaleOverviewResponse | null = null;
	let overviewLoading = false;
	let overviewError: string | null = null;

	let bayMetrics: ScaleBayMetricsResponse | null = null;
	let bayMetricsLoading = false;
	let bayMetricsError: string | null = null;

	let bayTable: ScaleBayTableResponse | null = null;
	let bayTableLoading = false;
	let bayTableError: string | null = null;

	let binImages: ScaleBinImagesResponse | null = null;
	let binImagesLoading = false;
	let binImagesError: string | null = null;

	let cameraHealth: ScaleCameraHealthResponse | null = null;
	let cameraLoading = false;
	let cameraError: string | null = null;

	$: systemOptions = tenantConfig?.available_lines?.length ? tenantConfig.available_lines : [];
	$: rangeDays = rangeParams?.days ?? 7;
	$: rangeHours = rangeParams?.rangeHours;
	$: rangeKey = rangeHours ? `h${rangeHours}` : `d${rangeDays}`;
	$: snapshotItems = snapshot?.items || [];
	$: snapshotOrder = systemOptions.length ? systemOptions : snapshotItems.map((item) => item.system_id);
	$: orderedSnapshot = snapshotOrder
		.map((id) => snapshotItems.find((item) => item.system_id === id))
		.filter(Boolean);
	$: overviewSeries = overview?.series || [];
	$: fillCounts = overview?.fill_counts || {};
	$: bayRows = bayTable?.rows || [];
	$: binImagesList = binImages?.images || [];
	$: failureCounts = cameraHealth?.counts || [];
	$: failureRows = cameraHealth?.failures || [];
	$: maxFailureCount = failureCounts.reduce((max, item) => Math.max(max, item.count), 0);

	$: if (tenantId && tenantId !== currentTenantId && systemOptions.length > 0) {
		currentTenantId = tenantId;
		selectedSystem = systemOptions[0];
		selectedView = viewOptions[0];
		if (initialized) {
			loadSnapshot();
			refreshView();
		}
	}

	onMount(async () => {
		initialized = true;
		if (!selectedSystem && systemOptions.length > 0) {
			selectedSystem = systemOptions[0];
		}
		await loadSnapshot();
		await refreshView();
	});

	$: if (initialized && rangeKey !== lastRangeKey) {
		lastRangeKey = rangeKey;
		loadSnapshot();
		refreshView();
	}

	async function loadSnapshot() {
		snapshotLoading = true;
		snapshotError = null;
		try {
			snapshot = await getScaleSnapshot(token, tenantId, rangeDays, rangeHours);
		} catch (e) {
			snapshotError = e instanceof Error ? e.message : 'Failed to load snapshot';
		} finally {
			snapshotLoading = false;
		}
	}

	async function loadOverview() {
		if (!selectedSystem) return;
		overviewLoading = true;
		overviewError = null;
		try {
			overview = await getScaleOverview(token, tenantId, selectedSystem, rangeDays, rangeHours);
		} catch (e) {
			overviewError = e instanceof Error ? e.message : 'Failed to load overview';
		} finally {
			overviewLoading = false;
		}
	}

	async function loadBayData(bay: number) {
		if (!selectedSystem) return;
		bayMetricsLoading = true;
		bayMetricsError = null;
		bayTableLoading = true;
		bayTableError = null;
		binImagesLoading = true;
		binImagesError = null;
		try {
			const [metrics, table, images] = await Promise.all([
				getScaleBayMetrics(token, tenantId, selectedSystem, bay, rangeDays, rangeHours),
				getScaleBayTable(token, tenantId, selectedSystem, bay, rangeDays, rangeHours, 50),
				getScaleBinImages(token, tenantId, selectedSystem, bay, rangeDays, rangeHours, 15)
			]);
			bayMetrics = metrics;
			bayTable = table;
			binImages = images;
		} catch (e) {
			const message = e instanceof Error ? e.message : 'Failed to load bay data';
			bayMetricsError = message;
			bayTableError = message;
			binImagesError = message;
		} finally {
			bayMetricsLoading = false;
			bayTableLoading = false;
			binImagesLoading = false;
		}
	}

	async function loadCameraHealth() {
		if (!selectedSystem) return;
		cameraLoading = true;
		cameraError = null;
		try {
			cameraHealth = await getScaleCameraHealth(token, tenantId, selectedSystem, rangeDays, rangeHours, 50);
		} catch (e) {
			cameraError = e instanceof Error ? e.message : 'Failed to load camera health';
		} finally {
			cameraLoading = false;
		}
	}

	async function refreshView() {
		if (!initialized) return;
		if (selectedView === 'Overview') {
			await loadOverview();
		} else if (selectedView === 'Bay 1') {
			await loadBayData(1);
		} else if (selectedView === 'Bay 2') {
			await loadBayData(2);
		} else {
			await loadCameraHealth();
		}
	}

	function handleSystemChange(systemId: string) {
		selectedSystem = systemId;
		refreshView();
	}

	function handleViewChange(view: string) {
		selectedView = view;
		refreshView();
	}

	function handleUnitChange(unit: string) {
		weightUnit = unit;
	}

	function formatSnapshotWeight(weightLbs: number): number {
		if (weightUnit === 'Tons') {
			return Number((weightLbs / 2000).toFixed(1));
		}
		return Math.round(weightLbs);
	}

	function weightUnitLabel(): string {
		return weightUnit === 'Tons' ? 'tons' : 'lbs';
	}

	function changeChip(change: number | null) {
		if (change === null || change === undefined) return null;
		const rounded = change.toFixed(1);
		return `${change > 0 ? '+' : ''}${rounded}%`;
	}

	function changeColor(change: number | null) {
		if (change === null || change === undefined) return 'neutral';
		return change > 0 ? 'red' : 'green';
	}
</script>

<div class="space-y-6">
	<div class="space-y-3">
		<div class="flex items-center justify-between">
			<h2 class="text-lg font-semibold {isDark ? 'text-white' : 'text-gray-900'}">Snapshot</h2>
			<div class="flex items-center gap-2">
				{#each unitOptions as option}
					<button
						class="px-3 py-1 text-xs rounded-lg border transition-colors {weightUnit === option
							? 'bg-[#5CC9D3] text-white border-[#5CC9D3]'
							: isDark
								? 'bg-gray-800 text-gray-300 border-gray-700 hover:border-[#5CC9D3]'
								: 'bg-white text-gray-700 border-gray-300 hover:border-[#5CC9D3]'}"
						on:click={() => handleUnitChange(option)}
					>
						{option}
					</button>
				{/each}
			</div>
		</div>

		{#if snapshotLoading}
			<div class="flex items-center justify-center h-24">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
			</div>
		{:else if snapshotError}
			<div class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
				{snapshotError}
			</div>
		{:else}
			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
				{#each orderedSnapshot as item}
					{#if item}
						<MetricCard
							label={item.system_id}
							value={formatSnapshotWeight(item.total_weight)}
							subtitle={weightUnitLabel()}
							chipValue={changeChip(item.change_percent)}
							chipColor={changeColor(item.change_percent)}
							{isDark}
						/>
					{/if}
				{/each}
			</div>
		{/if}
	</div>

	<div class="space-y-3">
		<h3 class="text-lg font-semibold {isDark ? 'text-white' : 'text-gray-900'}">Metrics</h3>
		<ToggleBar options={systemOptions} selected={selectedSystem} onSelect={handleSystemChange} {isDark} />
		<ToggleBar options={viewOptions} selected={selectedView} onSelect={handleViewChange} {isDark} size="sm" />
	</div>

	{#if selectedView === 'Overview'}
		{#if overviewLoading}
			<div class="flex items-center justify-center h-24">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
			</div>
		{:else if overviewError}
			<div class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
				{overviewError}
			</div>
		{:else}
			<div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
				<div class="lg:col-span-2 p-4 rounded-lg border {isDark ? 'bg-gray-800/50 border-gray-700/50' : 'bg-white border-gray-200'}">
					<MultiLineChart
						title="Bays 1 & 2: Realtime Scale Weights"
						subtitle=""
						series={overviewSeries.map((series, index) => ({
							label: series.label,
							color: index === 0 ? chartColors.primary : '#F9A620',
							data: series.data
						}))}
						{isDark}
						height={260}
					/>
				</div>
				<div class="space-y-4">
					<MetricCard label="Bay 1 Fill Count" value={fillCounts.bay1 ?? 0} {isDark} />
					<MetricCard label="Bay 2 Fill Count" value={fillCounts.bay2 ?? 0} {isDark} />
				</div>
			</div>
		{/if}
	{:else if selectedView === 'Bay 1' || selectedView === 'Bay 2'}
		{#if bayMetricsLoading}
			<div class="flex items-center justify-center h-24">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
			</div>
		{:else if bayMetricsError}
			<div class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
				{bayMetricsError}
			</div>
		{:else if bayMetrics}
			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
				<MetricCard label="Total Net Weight (lbs)" value={Math.round(bayMetrics.total_net_weight)} {isDark} />
				<MetricCard label="Fill Count" value={bayMetrics.fill_count} {isDark} />
				<MetricCard label="Std Dev Tare Weight" value={bayMetrics.tare_stddev} {isDark} />
				<MetricCard label="Std Dev Net Weight" value={bayMetrics.net_stddev} {isDark} />
			</div>
		{/if}

		<div class="p-4 rounded-lg border {isDark ? 'bg-gray-800/50 border-gray-700/50' : 'bg-white border-gray-200'}">
			<h4 class="text-sm font-semibold mb-3 {isDark ? 'text-white' : 'text-gray-900'}">
				{selectedView} Table
			</h4>
			{#if bayTableLoading}
				<div class="flex items-center justify-center h-32">
					<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
				</div>
			{:else if bayTableError}
				<div class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
					{bayTableError}
				</div>
			{:else if bayRows.length === 0}
				<div class="p-8 text-center {isDark ? 'text-gray-400' : 'text-gray-500'}">
					<p class="text-sm">No fill rows found for the selected period</p>
				</div>
			{:else}
				<div class="overflow-x-auto">
					<table class="min-w-full text-sm text-left {isDark ? 'text-gray-300' : 'text-gray-600'}">
						<thead class="{isDark ? 'text-gray-400' : 'text-gray-500'}">
							<tr>
								<th class="py-2 pr-3">Box ID</th>
								<th class="py-2 pr-3">Net Weight</th>
								<th class="py-2 pr-3">Tare Weight</th>
								<th class="py-2 pr-3">Gross Weight</th>
								<th class="py-2 pr-3">Job Total</th>
								<th class="py-2 pr-3">Time</th>
								<th class="py-2 pr-3">Scale</th>
								<th class="py-2 pr-3">Fill Stamp</th>
								<th class="py-2 pr-3">Consecutive</th>
								<th class="py-2 pr-3">Box Star</th>
							</tr>
						</thead>
						<tbody class="divide-y {isDark ? 'divide-gray-700' : 'divide-gray-200'}">
							{#each bayRows as row}
								<tr>
									<td class="py-2 pr-3">{row.box_id ?? '-'}</td>
									<td class="py-2 pr-3">{row.net_weight ?? '-'}</td>
									<td class="py-2 pr-3">{row.tare_weight ?? '-'}</td>
									<td class="py-2 pr-3">{row.gross_weight ?? '-'}</td>
									<td class="py-2 pr-3">{row.job_total ?? '-'}</td>
									<td class="py-2 pr-3">{row.time}</td>
									<td class="py-2 pr-3">{row.scale_number ?? '-'}</td>
									<td class="py-2 pr-3">{row.fill_stamp ?? '-'}</td>
									<td class="py-2 pr-3">{row.consecutive_number ?? '-'}</td>
									<td class="py-2 pr-3">{row.box_star ?? '-'}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>

		<div class="space-y-3">
			<h4 class="text-sm font-semibold {isDark ? 'text-white' : 'text-gray-900'}">Bin Images</h4>
			<ScaleWeightBinImagesList
				images={binImagesList}
				{isDark}
				loading={binImagesLoading}
				error={binImagesError}
			/>
		</div>
	{:else}
		{#if cameraLoading}
			<div class="flex items-center justify-center h-24">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
			</div>
		{:else if cameraError}
			<div class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
				{cameraError}
			</div>
		{:else}
			<div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
				<div class="p-4 rounded-lg border {isDark ? 'bg-gray-800/50 border-gray-700/50' : 'bg-white border-gray-200'}">
					<h4 class="text-sm font-semibold mb-3 {isDark ? 'text-white' : 'text-gray-900'}">
						Camera Failures
					</h4>
					{#if failureCounts.length === 0}
						<p class="text-sm {isDark ? 'text-gray-400' : 'text-gray-500'}">No failures recorded</p>
					{:else}
						{#each failureCounts as item}
							<div class="flex items-center gap-3 mb-3">
								<span class="text-xs w-16 {isDark ? 'text-gray-400' : 'text-gray-500'}">
									{item.label}
								</span>
								<div class="flex-1 h-2 rounded-full {isDark ? 'bg-gray-700' : 'bg-gray-200'}">
									<div
										class="h-2 rounded-full bg-[#5CC9D3]"
										style={`width:${maxFailureCount ? (item.count / maxFailureCount) * 100 : 0}%`}
									></div>
								</div>
								<span class="text-xs font-semibold {isDark ? 'text-white' : 'text-gray-900'}">
									{item.count}
								</span>
							</div>
						{/each}
					{/if}
				</div>

				<div class="p-4 rounded-lg border {isDark ? 'bg-gray-800/50 border-gray-700/50' : 'bg-white border-gray-200'}">
					<h4 class="text-sm font-semibold mb-3 {isDark ? 'text-white' : 'text-gray-900'}">
						Number of Failures
					</h4>
					{#if failureCounts.length === 0}
						<p class="text-sm {isDark ? 'text-gray-400' : 'text-gray-500'}">No failures recorded</p>
					{:else}
						<div class="grid grid-cols-2 gap-4">
							{#each failureCounts as item}
								<div class="space-y-1">
									<span class="text-xs {isDark ? 'text-gray-400' : 'text-gray-500'}">
										{item.label}
									</span>
									<span class="text-2xl font-bold {isDark ? 'text-white' : 'text-gray-900'}">
										{item.count}
									</span>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			</div>

			<div class="p-4 rounded-lg border {isDark ? 'bg-gray-800/50 border-gray-700/50' : 'bg-white border-gray-200'}">
				<h4 class="text-sm font-semibold mb-3 {isDark ? 'text-white' : 'text-gray-900'}">
					Camera Failures
				</h4>
				{#if failureRows.length === 0}
					<p class="text-sm {isDark ? 'text-gray-400' : 'text-gray-500'}">No failure rows found</p>
				{:else}
					<div class="overflow-x-auto">
						<table class="min-w-full text-sm text-left {isDark ? 'text-gray-300' : 'text-gray-600'}">
							<thead class="{isDark ? 'text-gray-400' : 'text-gray-500'}">
								<tr>
									<th class="py-2 pr-3">Host</th>
									<th class="py-2 pr-3">Time</th>
									<th class="py-2 pr-3">Device</th>
									<th class="py-2 pr-3">Exception</th>
									<th class="py-2 pr-3">Message</th>
									<th class="py-2 pr-3">Failed</th>
								</tr>
							</thead>
							<tbody class="divide-y {isDark ? 'divide-gray-700' : 'divide-gray-200'}">
								{#each failureRows as row}
									<tr>
										<td class="py-2 pr-3">{row.host ?? '-'}</td>
										<td class="py-2 pr-3">{row.time}</td>
										<td class="py-2 pr-3">{row.device_id ?? '-'}</td>
										<td class="py-2 pr-3">{row.exception ?? '-'}</td>
										<td class="py-2 pr-3">{row.message ?? '-'}</td>
										<td class="py-2 pr-3">{row.failed ?? '-'}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{/if}
			</div>
		{/if}
	{/if}
</div>
