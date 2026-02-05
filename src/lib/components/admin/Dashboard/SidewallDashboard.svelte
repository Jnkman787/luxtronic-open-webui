<script lang="ts">
	import { onMount } from 'svelte';
	import ToggleBar from './Toggle/ToggleBar.svelte';
	import DPMOCard from './Cards/DPMOCard.svelte';
	import MetricCard from './Cards/MetricCard.svelte';
	import LineChart from './Charts/LineChart.svelte';
	import MultiLineChart from './Charts/MultiLineChart.svelte';
	import SidewallIncidentsList from './Incidents/SidewallIncidentsList.svelte';
	import {
		getSidewallSnapshot,
		getSidewallInspections,
		getSidewallDefect,
		getSidewallIncidents,
		getSidewallHealth,
		type TenantDashboardConfig,
		type SidewallSnapshotResponse,
		type SidewallInspectionsResponse,
		type SidewallDefectResponse,
		type SystemHealthResponse,
		type Incident
	} from '$lib/apis/dashboard';
	import { chartColors } from '$lib/stores/dashboard';

	export let token: string;
	export let tenantId: string;
	export let rangeLabel: string;
	export let rangeParams: { days?: number; rangeHours?: number };
	export let isDark: boolean = false;
	export let tenantConfig: TenantDashboardConfig | null = null;

	const DPMO_HELP =
		'Defects per million inspections: (defects / total inspections) x 1,000,000 over the selected time range.';
	const defaultDefectClasses = ['critical', 'blister', 'stone', 'cosmetic'];

	let selectedView = 'Inspections';
	let currentTenantId = '';
	let lastRangeKey = '';
	let initialized = false;

	let snapshot: SidewallSnapshotResponse | null = null;
	let snapshotLoading = false;
	let snapshotError: string | null = null;
	let snapshotRequestId = 0;

	let inspections: SidewallInspectionsResponse | null = null;
	let inspectionsLoading = false;
	let inspectionsError: string | null = null;
	let inspectionsRequestId = 0;

	let defectDetail: SidewallDefectResponse | null = null;
	let defectLoading = false;
	let defectError: string | null = null;
	let defectRequestId = 0;

	let systemHealth: SystemHealthResponse | null = null;
	let systemHealthLoading = false;
	let systemHealthError: string | null = null;
	let systemHealthRequestId = 0;

	let incidentsByClass: Record<string, Incident[]> = {};
	let incidentsLoading = false;
	let incidentsError: string | null = null;
	let incidentsRequestId = 0;

	$: defectClasses = (tenantConfig?.defect_classes || []).length
		? (tenantConfig?.defect_classes || []).map((value) => value.toLowerCase())
		: defaultDefectClasses;
	$: defectLabels = defectClasses.map((value) => formatLabel(value));
	$: viewOptions = ['Inspections', ...defectLabels, 'System Health'];
	$: defectClassByLabel = Object.fromEntries(defectClasses.map((value) => [formatLabel(value), value]));
	$: defectTotals = snapshot?.defects || [];
	$: defectTotalsMap = Object.fromEntries(
		defectTotals.map((item) => [item.defect_class.toLowerCase(), item.total])
	);
	$: rangeDays = rangeParams?.days ?? 7;
	$: rangeHours = rangeParams?.rangeHours;
	$: rangeKey = rangeHours ? `h${rangeHours}` : `d${rangeDays}`;
	$: if (!viewOptions.includes(selectedView)) {
		selectedView = 'Inspections';
	}

	onMount(async () => {
		initialized = true;
		await loadSnapshot();
		await refreshView();
		await loadIncidents();
	});

	$: if (tenantId && tenantId !== currentTenantId) {
		currentTenantId = tenantId;
		selectedView = 'Inspections';
		if (initialized) {
			loadSnapshot();
			refreshView();
			loadIncidents();
		}
	}

	$: if (initialized && rangeKey !== lastRangeKey) {
		lastRangeKey = rangeKey;
		loadSnapshot();
		refreshView();
		loadIncidents();
	}

	function formatLabel(value: string): string {
		return value
			.replace(/_/g, ' ')
			.replace(/\b\w/g, (char) => char.toUpperCase());
	}

	function formatPercent(value: number | null | undefined): string {
		if (value === null || value === undefined) return 'N/A';
		return `${(value * 100).toFixed(2)}%`;
	}

	async function loadSnapshot() {
		if (!tenantId) return;
		snapshotLoading = true;
		snapshotError = null;
		const requestId = ++snapshotRequestId;
		try {
			const response = await getSidewallSnapshot(token, tenantId, rangeDays, rangeHours);
			if (requestId !== snapshotRequestId) return;
			snapshot = response;
		} catch (e) {
			if (requestId !== snapshotRequestId) return;
			snapshotError = e instanceof Error ? e.message : 'Failed to load snapshot';
		} finally {
			if (requestId === snapshotRequestId) snapshotLoading = false;
		}
	}

	async function loadInspections() {
		if (!tenantId) return;
		inspectionsLoading = true;
		inspectionsError = null;
		const requestId = ++inspectionsRequestId;
		try {
			const response = await getSidewallInspections(token, tenantId, rangeDays, rangeHours);
			if (requestId !== inspectionsRequestId) return;
			inspections = response;
		} catch (e) {
			if (requestId !== inspectionsRequestId) return;
			inspectionsError = e instanceof Error ? e.message : 'Failed to load inspections';
		} finally {
			if (requestId === inspectionsRequestId) inspectionsLoading = false;
		}
	}

	async function loadDefect(defectClass: string) {
		if (!tenantId || !defectClass) return;
		defectLoading = true;
		defectError = null;
		const requestId = ++defectRequestId;
		try {
			const response = await getSidewallDefect(token, tenantId, defectClass, rangeDays, rangeHours);
			if (requestId !== defectRequestId) return;
			defectDetail = response;
		} catch (e) {
			if (requestId !== defectRequestId) return;
			defectError = e instanceof Error ? e.message : 'Failed to load defect metrics';
		} finally {
			if (requestId === defectRequestId) defectLoading = false;
		}
	}

	async function loadSystemHealth() {
		if (!tenantId) return;
		systemHealthLoading = true;
		systemHealthError = null;
		const requestId = ++systemHealthRequestId;
		try {
			const response = await getSidewallHealth(token, tenantId);
			if (requestId !== systemHealthRequestId) return;
			systemHealth = response;
		} catch (e) {
			if (requestId !== systemHealthRequestId) return;
			systemHealthError = e instanceof Error ? e.message : 'Failed to load system health';
		} finally {
			if (requestId === systemHealthRequestId) systemHealthLoading = false;
		}
	}

	async function loadIncidents() {
		if (!tenantId || defectClasses.length === 0) return;
		incidentsLoading = true;
		incidentsError = null;
		const requestId = ++incidentsRequestId;
		try {
			const responses = await Promise.all(
				defectClasses.map((defectClass) =>
					getSidewallIncidents(token, tenantId, defectClass, rangeDays, 10, rangeHours)
				)
			);
			if (requestId !== incidentsRequestId) return;
			const incidentMap: Record<string, Incident[]> = {};
			responses.forEach((response, index) => {
				incidentMap[defectClasses[index]] = response.incidents || [];
			});
			incidentsByClass = incidentMap;
		} catch (e) {
			if (requestId !== incidentsRequestId) return;
			incidentsError = e instanceof Error ? e.message : 'Failed to load incidents';
		} finally {
			if (requestId === incidentsRequestId) incidentsLoading = false;
		}
	}

	async function refreshView() {
		if (!initialized) return;
		if (selectedView === 'Inspections') {
			await loadInspections();
			return;
		}
		if (selectedView === 'System Health') {
			await loadSystemHealth();
			return;
		}
		const defectClass = defectClassByLabel[selectedView];
		if (defectClass) {
			await loadDefect(defectClass);
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
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
				<DPMOCard
					line="Sidewall"
					dpmo={snapshot?.dpmo ?? null}
					totalUnits={snapshot?.total_inspections ?? null}
					dpmoHelpText={DPMO_HELP}
					{isDark}
				/>
				{#each defectClasses as defectClass}
					<MetricCard
						label={formatLabel(defectClass)}
						value={defectTotalsMap[defectClass] ?? 0}
						{isDark}
					/>
				{/each}
			</div>
		{/if}
	</div>

	<div class="space-y-3">
		<h3 class="text-lg font-semibold {isDark ? 'text-white' : 'text-gray-900'}">Metrics</h3>
		<ToggleBar options={viewOptions} selected={selectedView} onSelect={handleViewChange} {isDark} />
	</div>

	{#if selectedView === 'Inspections'}
		{#if inspectionsLoading}
			<div class="flex items-center justify-center h-20">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
			</div>
		{:else if inspectionsError}
			<div class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
				{inspectionsError}
			</div>
		{:else if inspections}
			<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
				<MetricCard label="Total Inspections" value={inspections.total_inspections} {isDark} />
				<MetricCard
					label="Total Jars"
					value={inspections.total_jars !== null && inspections.total_jars !== undefined
						? inspections.total_jars.toFixed(1)
						: 'N/A'}
					{isDark}
				/>
				<MetricCard
					label="Rejections"
					value={inspections.total_rejects}
					chipValue={formatPercent(inspections.reject_rate)}
					chipColor="red"
					{isDark}
				/>
			</div>
		{/if}

		<div class="p-4 rounded-lg border {isDark ? 'bg-gray-800/50 border-gray-700/50' : 'bg-white border-gray-200'}">
			<LineChart
				title="Inspections Trend"
				subtitle={rangeLabel}
				data={inspections?.trend || []}
				color={chartColors.primary}
				{isDark}
				height={250}
			/>
		</div>
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
	{:else}
		{#if defectLoading}
			<div class="flex items-center justify-center h-20">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
			</div>
		{:else if defectError}
			<div class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
				{defectError}
			</div>
		{:else if defectDetail}
			<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
				<MetricCard label="Total" value={defectDetail.total_defects} {isDark} />
				<MetricCard label="Rate by inspections" value={formatPercent(defectDetail.rate_by_inspections)} {isDark} />
				<MetricCard label="% of all defects" value={formatPercent(defectDetail.percent_of_defects)} {isDark} />
			</div>
		{/if}

		<div class="p-4 rounded-lg border {isDark ? 'bg-gray-800/50 border-gray-700/50' : 'bg-white border-gray-200'}">
			<MultiLineChart
				title="Defect Trend"
				subtitle={rangeLabel}
				series={(defectDetail?.series || []).map((series, index) => ({
					label: series.label,
					color: [chartColors.line1, chartColors.line2, chartColors.line3, chartColors.line4][index % 4],
					data: series.data
				}))}
				{isDark}
				height={250}
			/>
		</div>
	{/if}

	<div class="space-y-3">
		<h3 class="text-sm font-semibold {isDark ? 'text-white' : 'text-gray-900'}">
			Recent Incidents ({rangeLabel})
		</h3>
		{#if incidentsLoading}
			<div class="flex items-center justify-center h-24">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
			</div>
		{:else if incidentsError}
			<div class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
				{incidentsError}
			</div>
		{:else}
			<div class="space-y-4">
				{#each defectClasses as defectClass}
					<SidewallIncidentsList
						title={formatLabel(defectClass)}
						incidents={incidentsByClass[defectClass] || []}
						{isDark}
					/>
				{/each}
			</div>
		{/if}
	</div>
</div>
