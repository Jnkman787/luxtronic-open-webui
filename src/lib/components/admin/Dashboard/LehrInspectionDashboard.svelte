<script lang="ts">
	import { onMount } from 'svelte';
	import ToggleBar from './Toggle/ToggleBar.svelte';
	import MetricCard from './Cards/MetricCard.svelte';
	import LineChart from './Charts/LineChart.svelte';
	import MultiLineChart from './Charts/MultiLineChart.svelte';
	import LehrIncidentsList from './Incidents/LehrIncidentsList.svelte';
	import {
		getLehrSnapshot,
		getLehrOverhead,
		getLehrExit,
		getLehrDumpGate,
		getLehrIncidents,
		getSystemHealth,
		type LehrSnapshotResponse,
		type LehrMetricsResponse,
		type LehrDumpGateResponse,
		type LehrIncidentsResponse,
		type LehrMetricSeries,
		type SystemHealthResponse,
		type TenantDashboardConfig
	} from '$lib/apis/dashboard';

	export let token: string;
	export let tenantId: string;
	export let rangeLabel: string;
	export let rangeParams: { days?: number; rangeHours?: number };
	export let isDark: boolean = false;
	export let tenantConfig: TenantDashboardConfig | null = null;

	const viewOptions = ['Overhead', 'Exit', 'Down/Empty', 'System Health'];
	const metricColors: Record<string, string> = {
		ring: '#5CC9D3',
		down: '#FF6B35',
		empty_mat: '#F9A620',
		empty: '#F9A620'
	};
	const metricLabels: Record<string, string> = {
		ring: 'Ring',
		down: 'Down',
		empty_mat: 'Empty',
		empty: 'Empty'
	};

	let selectedView = viewOptions[0];
	let initialized = false;
	let lastRangeKey = '';

	let snapshot: LehrSnapshotResponse | null = null;
	let snapshotLoading = false;
	let snapshotError: string | null = null;

	let overhead: LehrMetricsResponse | null = null;
	let overheadLoading = false;
	let overheadError: string | null = null;

	let exitMetrics: LehrMetricsResponse | null = null;
	let exitLoading = false;
	let exitError: string | null = null;

	let dumpGate: LehrDumpGateResponse | null = null;
	let dumpGateLoading = false;
	let dumpGateError: string | null = null;

	let incidents: LehrIncidentsResponse | null = null;
	let incidentsLoading = false;
	let incidentsError: string | null = null;

	let systemHealth: SystemHealthResponse | null = null;
	let systemHealthLoading = false;
	let systemHealthError: string | null = null;

	$: rangeDays = rangeParams?.days ?? 7;
	$: rangeHours = rangeParams?.rangeHours;
	$: rangeKey = rangeHours ? `h${rangeHours}` : `d${rangeDays}`;

	onMount(async () => {
		initialized = true;
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

	function mapSeries(series: LehrMetricSeries[] = []) {
		return series.map((line) => ({
			label: metricLabels[line.label] || line.label,
			color: metricColors[line.label] || '#5CC9D3',
			data: line.data
		}));
	}

	function formatDuration(seconds: number | null | undefined): string {
		const total = seconds ?? 0;
		const hours = Math.floor(total / 3600);
		const minutes = Math.floor((total % 3600) / 60);
		return `${hours}h ${minutes}m`;
	}

	async function loadSnapshot() {
		snapshotLoading = true;
		snapshotError = null;
		try {
			snapshot = await getLehrSnapshot(token, tenantId, rangeDays, rangeHours);
		} catch (e) {
			snapshotError = e instanceof Error ? e.message : 'Failed to load snapshot';
		} finally {
			snapshotLoading = false;
		}
	}

	async function loadOverhead() {
		overheadLoading = true;
		overheadError = null;
		try {
			overhead = await getLehrOverhead(token, tenantId, rangeDays, rangeHours);
		} catch (e) {
			overheadError = e instanceof Error ? e.message : 'Failed to load overhead metrics';
		} finally {
			overheadLoading = false;
		}
	}

	async function loadExit() {
		exitLoading = true;
		exitError = null;
		try {
			exitMetrics = await getLehrExit(token, tenantId, rangeDays, rangeHours);
		} catch (e) {
			exitError = e instanceof Error ? e.message : 'Failed to load exit metrics';
		} finally {
			exitLoading = false;
		}
	}

	async function loadDumpGate() {
		dumpGateLoading = true;
		dumpGateError = null;
		try {
			dumpGate = await getLehrDumpGate(token, tenantId, rangeDays, rangeHours);
		} catch (e) {
			dumpGateError = e instanceof Error ? e.message : 'Failed to load dump gate metrics';
		} finally {
			dumpGateLoading = false;
		}
	}

	async function loadIncidents() {
		incidentsLoading = true;
		incidentsError = null;
		try {
			incidents = await getLehrIncidents(token, tenantId, rangeDays, rangeHours, 30);
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
			systemHealth = await getSystemHealth(token, tenantId, 30);
		} catch (e) {
			systemHealthError = e instanceof Error ? e.message : 'Failed to load system health';
		} finally {
			systemHealthLoading = false;
		}
	}

	async function refreshView() {
		if (!initialized) return;
		if (selectedView === 'Overhead' || selectedView === 'Down/Empty') {
			await loadOverhead();
		} else if (selectedView === 'Exit') {
			await Promise.all([loadExit(), loadDumpGate()]);
		} else if (selectedView === 'System Health') {
			await loadSystemHealth();
		} else {
			await loadOverhead();
		}
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
			<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
				<MetricCard label="Lehr Exit" value={snapshot?.total_units ?? 0} {isDark} />
				<MetricCard label="Down" value={snapshot?.down_units ?? 0} {isDark} />
				<MetricCard label="Empty" value={snapshot?.empty_units ?? 0} {isDark} />
			</div>
		{/if}
	</div>

	<div class="space-y-3">
		<h3 class="text-lg font-semibold {isDark ? 'text-white' : 'text-gray-900'}">Metrics</h3>
		<ToggleBar options={viewOptions} selected={selectedView} onSelect={handleViewChange} {isDark} />
		<p class="text-xs {isDark ? 'text-gray-400' : 'text-gray-500'}">{rangeLabel}</p>
	</div>

	{#if selectedView === 'Overhead'}
		{#if overheadLoading}
			<div class="flex items-center justify-center h-24">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
			</div>
		{:else if overheadError}
			<div class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
				{overheadError}
			</div>
		{:else if overhead}
			<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
				<MetricCard label="Total" value={overhead.totals.ring} {isDark} />
				<MetricCard label="Down" value={overhead.totals.down} {isDark} />
				<MetricCard label="Empty" value={overhead.totals.empty ?? 0} {isDark} />
			</div>

			<div class="p-4 rounded-lg border {isDark ? 'bg-gray-800/50 border-gray-700/50' : 'bg-white border-gray-200'}">
				<MultiLineChart
					title="Production Trend"
					subtitle={rangeLabel}
					series={mapSeries(overhead.trend)}
					{isDark}
					height={250}
				/>
			</div>
		{/if}
	{:else if selectedView === 'Exit'}
		{#if exitLoading}
			<div class="flex items-center justify-center h-24">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
			</div>
		{:else if exitError}
			<div class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
				{exitError}
			</div>
		{:else if exitMetrics}
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<MetricCard label="Total" value={exitMetrics.totals.ring} {isDark} />
				<MetricCard label="Down" value={exitMetrics.totals.down} {isDark} />
			</div>

			<div class="p-4 rounded-lg border {isDark ? 'bg-gray-800/50 border-gray-700/50' : 'bg-white border-gray-200'}">
				<MultiLineChart
					title="Lehr Exit Production Trend"
					subtitle={rangeLabel}
					series={mapSeries(exitMetrics.trend)}
					{isDark}
					height={250}
				/>
			</div>

			<div class="space-y-3">
				<h4 class="text-base font-semibold {isDark ? 'text-white' : 'text-gray-900'}">Dump Gate</h4>
				{#if dumpGateLoading}
					<div class="flex items-center justify-center h-20">
						<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
					</div>
				{:else if dumpGateError}
					<div class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
						{dumpGateError}
					</div>
				{:else if dumpGate}
					<div class="grid grid-cols-1 md:grid-cols-4 gap-4">
						<MetricCard label="Down" value={dumpGate.total_down} {isDark} />
						<MetricCard label="Total" value={dumpGate.total_ring} {isDark} />
						<MetricCard label="Lost" value={dumpGate.total_lost} {isDark} />
						<MetricCard label="Open Time" value={formatDuration(dumpGate.open_seconds)} {isDark} />
					</div>

					<div class="p-4 rounded-lg border {isDark ? 'bg-gray-800/50 border-gray-700/50' : 'bg-white border-gray-200'}">
						<LineChart
							title="Dump Gate Open Time"
							subtitle={rangeLabel}
							data={dumpGate.open_trend}
							color="#5CC9D3"
							{isDark}
							height={250}
							showDots={true}
						/>
					</div>
				{/if}
			</div>
		{/if}
	{:else if selectedView === 'Down/Empty'}
		{#if overheadLoading}
			<div class="flex items-center justify-center h-24">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
			</div>
		{:else if overheadError}
			<div class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
				{overheadError}
			</div>
		{:else if overhead}
			<div class="p-4 rounded-lg border {isDark ? 'bg-gray-800/50 border-gray-700/50' : 'bg-white border-gray-200'}">
				<MultiLineChart
					title="Down and Empty Location"
					subtitle={rangeLabel}
					series={mapSeries(overhead.locations)}
					{isDark}
					height={250}
					showLines={false}
					showDots={true}
				/>
			</div>
		{/if}
	{:else if selectedView === 'System Health'}
		<div class="space-y-4">
			{#if systemHealthLoading}
				<div class="flex items-center justify-center h-32">
					<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
				</div>
			{:else if systemHealthError}
				<div class="p-4 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
					{systemHealthError}
				</div>
			{:else if !systemHealth || systemHealth.devices.length === 0}
				<div class="p-8 text-center {isDark ? 'text-gray-400' : 'text-gray-500'}">
					<p class="text-sm">No device health data available</p>
				</div>
			{:else}
				<div class="flex items-center justify-between mb-2">
					<h4 class="text-sm font-medium {isDark ? 'text-white' : 'text-gray-900'}">
						Device Status
					</h4>
					{#if systemHealth?.timestamp}
						<span class="text-xs {isDark ? 'text-gray-500' : 'text-gray-400'}">
							Updated: {new Date(systemHealth.timestamp).toLocaleTimeString()}
						</span>
					{/if}
				</div>
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
					{#each systemHealth.devices as device}
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
									<span class="{isDark ? 'text-gray-300' : 'text-gray-700'}">
										{device.system.toUpperCase()}
									</span>
								</div>
								{#if device.latest_fps !== null}
									<div class="flex justify-between">
										<span>Rate:</span>
										<span class="{isDark ? 'text-gray-300' : 'text-gray-700'}">
											{device.latest_fps.toFixed(1)}
										</span>
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
									<p
										class="mt-1 text-xs italic {device.status === 'error'
											? 'text-red-400'
											: device.status === 'warning'
												? 'text-yellow-400'
												: ''}"
									>
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
		<LehrIncidentsList
			incidents={incidents?.incidents || []}
			{isDark}
			loading={incidentsLoading}
			error={incidentsError}
		/>
	</div>
</div>
