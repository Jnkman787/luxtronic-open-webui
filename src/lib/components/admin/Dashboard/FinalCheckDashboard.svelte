<script lang="ts">
	import { onMount } from 'svelte';
	import ToggleBar from './Toggle/ToggleBar.svelte';
	import MetricCard from './Cards/MetricCard.svelte';
	import FinalCheckIncidentsList from './Incidents/FinalCheckIncidentsList.svelte';
	import {
		getFinalCheckSnapshot,
		getFinalCheckDefects,
		getFinalCheckIncidents,
		getSystemHealth,
		type FinalCheckSnapshotResponse,
		type FinalCheckDefectsResponse,
		type FinalCheckIncidentsResponse,
		type SystemHealthResponse
	} from '$lib/apis/dashboard';

	export let token: string;
	export let tenantId: string;
	export let lineId: string | null = null;
	export let rangeLabel: string;
	export let rangeParams: { days?: number; rangeHours?: number };
	export let isDark: boolean = false;

	const viewOptions = ['Defects', 'System'];
	const barColors = ['#5CC9D3', '#F9A620', '#FF6B35'];
	const chartHeight = 220;

	let selectedView = viewOptions[0];
	let initialized = false;
	let lastRangeKey = '';
	let currentLineId = '';

	let snapshot: FinalCheckSnapshotResponse | null = null;
	let snapshotLoading = false;
	let snapshotError: string | null = null;

	let defects: FinalCheckDefectsResponse | null = null;
	let defectsLoading = false;
	let defectsError: string | null = null;

	let incidents: FinalCheckIncidentsResponse | null = null;
	let incidentsLoading = false;
	let incidentsError: string | null = null;

	let systemHealth: SystemHealthResponse | null = null;
	let systemHealthLoading = false;
	let systemHealthError: string | null = null;
	let systemHealthTimestamp = '';

	$: rangeDays = rangeParams?.days ?? 7;
	$: rangeHours = rangeParams?.rangeHours;
	$: rangeKey = rangeHours ? `h${rangeHours}` : `d${rangeDays}`;
	$: activeLineId = (lineId || 'CX').toUpperCase();
	$: systemHealthDevices = (systemHealth?.devices || []).filter(
		(device) => (device.line_id || '').toUpperCase() === activeLineId
	);

	$: defectBars = defects?.defects || [];
	$: paddedBars = padBars(defectBars, 9);
	$: maxCount = Math.max(1, ...paddedBars.map((bar) => bar.count || 0));
	$: yTicks = buildTicks(maxCount, 4);

	onMount(async () => {
		initialized = true;
		lastRangeKey = rangeKey;
		currentLineId = activeLineId;
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

	$: if (initialized && activeLineId !== currentLineId) {
		currentLineId = activeLineId;
		loadSnapshot();
		refreshView();
		loadIncidents();
	}

	function padBars(bars: { label: string; count: number }[], total: number) {
		const padded = [...bars];
		while (padded.length < total) {
			padded.push({ label: '', count: 0 });
		}
		return padded.slice(0, total);
	}

	function buildTicks(maxValue: number, segments: number) {
		const ticks = [];
		for (let i = 0; i <= segments; i += 1) {
			const value = Math.round((maxValue * (segments - i)) / segments);
			const y = (chartHeight * i) / segments;
			ticks.push({ value, y });
		}
		return ticks;
	}

	function formatCount(value: number) {
		if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
		if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
		return value.toString();
	}

	async function loadSnapshot() {
		snapshotLoading = true;
		snapshotError = null;
		try {
			snapshot = await getFinalCheckSnapshot(token, tenantId, activeLineId, rangeDays, rangeHours);
		} catch (e) {
			snapshotError = e instanceof Error ? e.message : 'Failed to load snapshot';
		} finally {
			snapshotLoading = false;
		}
	}

	async function loadDefects() {
		defectsLoading = true;
		defectsError = null;
		try {
			defects = await getFinalCheckDefects(token, tenantId, activeLineId, rangeDays, rangeHours, 9);
		} catch (e) {
			defectsError = e instanceof Error ? e.message : 'Failed to load defect data';
		} finally {
			defectsLoading = false;
		}
	}

	async function loadIncidents() {
		incidentsLoading = true;
		incidentsError = null;
		try {
			incidents = await getFinalCheckIncidents(token, tenantId, activeLineId, rangeDays, rangeHours, 200);
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
			systemHealthTimestamp = systemHealth?.timestamp || '';
		} catch (e) {
			systemHealthError = e instanceof Error ? e.message : 'Failed to load system health';
		} finally {
			systemHealthLoading = false;
		}
	}

	async function refreshView() {
		if (!initialized) return;
		if (selectedView === 'Defects') {
			await loadDefects();
		} else {
			await loadSystemHealth();
		}
	}

	function handleViewChange(view: string) {
		selectedView = view;
		refreshView();
	}
</script>

<div class="space-y-6">
	<div class="space-y-3">
		<h2 class="text-lg font-semibold {isDark ? 'text-white' : 'text-gray-900'}">Snapshot</h2>
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
				<MetricCard label="Accumulation Incidents" value={snapshot?.counts.accumulation ?? 0} {isDark} />
				<MetricCard label="Divider Incidents" value={snapshot?.counts.divider ?? 0} {isDark} />
				<MetricCard label="Slipsheet/Canpack Incidents" value={snapshot?.counts.slipsheet ?? 0} {isDark} />
			</div>
		{/if}
	</div>

	<div class="space-y-3">
		<h3 class="text-lg font-semibold {isDark ? 'text-white' : 'text-gray-900'}">Line Metrics</h3>
		<ToggleBar options={viewOptions} selected={selectedView} onSelect={handleViewChange} {isDark} />
		<p class="text-xs {isDark ? 'text-gray-400' : 'text-gray-500'}">{rangeLabel}</p>
	</div>

	{#if selectedView === 'Defects'}
		{#if defectsLoading}
			<div class="flex items-center justify-center h-32">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
			</div>
		{:else if defectsError}
			<div class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
				{defectsError}
			</div>
		{:else}
			<div class="p-4 rounded-lg border {isDark ? 'bg-gray-800/50 border-gray-700/50' : 'bg-white border-gray-200'}">
				<h4 class="text-sm font-semibold mb-2 {isDark ? 'text-white' : 'text-gray-900'}">Defect Type</h4>
				<div class="flex gap-3">
					<div class="flex flex-col justify-between text-xs pr-2 {isDark ? 'text-gray-400' : 'text-gray-500'}" style="height: {chartHeight}px;">
						{#each yTicks as tick}
							<span>{formatCount(tick.value)}</span>
						{/each}
					</div>
					<div class="flex-1">
						<div class="relative" style="height: {chartHeight}px;">
							<div class="absolute inset-0 flex flex-col justify-between">
								{#each yTicks as tick}
									<div class="border-t {isDark ? 'border-gray-700/70' : 'border-gray-200'}" style="top: {tick.y}px;"></div>
								{/each}
							</div>
							<div class="absolute inset-0 flex items-end gap-3 px-3">
								{#each paddedBars as bar, index}
									<div class="flex flex-col items-center justify-end h-full">
										<div
											class="w-6 rounded-t"
											style="height: {Math.round((bar.count / maxCount) * chartHeight)}px; background: {barColors[index % barColors.length]};"
										></div>
										<span class="mt-1 text-[10px] {isDark ? 'text-gray-400' : 'text-gray-500'}">
											{bar.label || index + 1}
										</span>
									</div>
								{/each}
							</div>
						</div>
					</div>
				</div>
			</div>
		{/if}
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
			{:else if systemHealthDevices.length === 0}
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
					{#each systemHealthDevices as device}
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

	<div class="space-y-3 mt-6">
		<h4 class="text-sm font-semibold {isDark ? 'text-white' : 'text-gray-900'}">
			Recent Incidents ({rangeLabel})
		</h4>
		<FinalCheckIncidentsList
			incidents={incidents?.incidents || []}
			{isDark}
			loading={incidentsLoading}
			error={incidentsError}
		/>
	</div>
</div>
