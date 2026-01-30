<script lang="ts">
	import MetricCard from './Cards/MetricCard.svelte';
	import MultiLineChart from './Charts/MultiLineChart.svelte';
	import ShiftIncidentsList from './Incidents/ShiftIncidentsList.svelte';
	import { shiftRangeOptions, type ShiftRangeOption } from './shiftRangeOptions';

	import {
		getShiftSnapshot,
		getShiftThroughput,
		getShiftDown,
		getShiftTimeSeries,
		getShiftIncidents,
		type TenantDashboardConfig,
		type ShiftSnapshotItem,
		type ShiftThroughputResponse,
		type ShiftDownItem,
		type ShiftSeries,
		type Incident
	} from '$lib/apis/dashboard';
	import { chartColors } from '$lib/stores/dashboard';

	export let token: string;
	export let tenantId: string;
	export let tenantConfig: TenantDashboardConfig | null = null;
	export let isDark: boolean = false;

	export let rangeOptions: ShiftRangeOption[] = shiftRangeOptions;
	export let rangeSelection = 'shift';
	export let includeBothShifts = false;

	let currentTenantId = '';
	let selectedLine = '';
	let shiftHours = 12;
	let binMinutes = 10;
	let lastRangeSelection = rangeSelection;
	let lastLineSelection = '';

	let snapshotTotals: ShiftSnapshotItem[] = [];
	let shiftLabel = '';
	let snapshotLoading = false;
	let snapshotError: string | null = null;
	let snapshotRequestId = 0;

	let throughput: ShiftThroughputResponse | null = null;
	let downTotals: ShiftDownItem[] = [];
	let timeSeries: ShiftSeries[] = [];
	let lineLoading = false;
	let lineError: string | null = null;
	let lineRequestId = 0;

	let incidents: Incident[] = [];
	let incidentsLoading = false;
	let incidentsError: string | null = null;
	let incidentsRequestId = 0;

	$: lineOptions = tenantConfig?.available_lines || [];
	$: chartSeries = timeSeries.map((series, index) => ({
		label: series.label,
		color: [chartColors.line1, chartColors.line2, chartColors.line3, chartColors.line4][index % 4],
		data: series.data
	}));
	$: timeseriesLineId =
		tenantConfig?.shift_timeseries_scope === 'all' ? '__all__' : selectedLine;
	$: rangeLabel =
		rangeOptions.find((item) => item.value === rangeSelection)?.label || 'Current shift (12h)';
	$: chartSubtitle = includeBothShifts
		? `${binMinutes}-minute buckets (${rangeLabel})`
		: `${binMinutes}-minute buckets (current ${shiftLabel ? `${shiftLabel} shift` : 'shift'})`;

	$: if (tenantConfig && tenantId && tenantId !== currentTenantId) {
		currentTenantId = tenantId;
		shiftHours = tenantConfig.shift_hours ?? 12;
		binMinutes = tenantConfig.shift_bin_minutes ?? 10;
		selectedLine = lineOptions[0] || '';
		lastLineSelection = selectedLine;
		includeBothShifts = false;
		rangeSelection = 'shift';
		lastRangeSelection = rangeSelection;
		loadSnapshot();
		loadLineData();
		loadIncidents();
	}

	$: if (lineOptions.length > 0 && selectedLine && !lineOptions.includes(selectedLine)) {
		selectedLine = lineOptions[0];
	}

	$: if (selectedLine && selectedLine !== lastLineSelection) {
		lastLineSelection = selectedLine;
		loadLineData();
		loadIncidents();
	}

	$: if (tenantId && currentTenantId && rangeSelection !== lastRangeSelection) {
		lastRangeSelection = rangeSelection;
		loadSnapshot();
		loadLineData();
		loadIncidents();
	}

	function getRangeParams() {
		const range = rangeOptions.find((item) => item.value === rangeSelection);
		return { rangeHours: range?.rangeHours, days: range?.days };
	}

	async function loadSnapshot() {
		if (!tenantId) return;

		snapshotLoading = true;
		snapshotError = null;
		const requestId = ++snapshotRequestId;

		try {
			const rangeParams = getRangeParams();
			const response = await getShiftSnapshot(token, tenantId, {
				shiftHours,
				shiftFilter: includeBothShifts ? 'all' : undefined,
				...rangeParams
			});
			if (requestId !== snapshotRequestId) return;
			snapshotTotals = response.totals;
			shiftLabel = response.shift_label;
		} catch (e) {
			if (requestId !== snapshotRequestId) return;
			snapshotError = e instanceof Error ? e.message : 'Failed to load shift snapshot';
			console.error('Shift snapshot error:', e);
		} finally {
			if (requestId === snapshotRequestId) snapshotLoading = false;
		}
	}

	async function loadLineData() {
		if (!tenantId || !selectedLine) return;

		lineLoading = true;
		lineError = null;
		throughput = null;
		downTotals = [];
		timeSeries = [];
		const requestId = ++lineRequestId;

		try {
			const rangeParams = getRangeParams();
			const [throughputResponse, downResponse, timeSeriesResponse] = await Promise.all([
				getShiftThroughput(token, tenantId, selectedLine, {
					shiftHours,
					shiftFilter: includeBothShifts ? 'all' : undefined,
					...rangeParams
				}),
				getShiftDown(token, tenantId, selectedLine, {
					shiftHours,
					shiftFilter: includeBothShifts ? 'all' : undefined,
					...rangeParams
				}),
				getShiftTimeSeries(token, tenantId, timeseriesLineId, 'total', {
					shiftHours,
					binMinutes,
					shiftFilter: includeBothShifts ? 'all' : undefined,
					...rangeParams
				})
			]);
			if (requestId !== lineRequestId) return;
			throughput = throughputResponse;
			downTotals = downResponse.totals;
			timeSeries = timeSeriesResponse.series;
		} catch (e) {
			if (requestId !== lineRequestId) return;
			lineError = e instanceof Error ? e.message : 'Failed to load shift data';
			console.error('Shift line data error:', e);
		} finally {
			if (requestId === lineRequestId) lineLoading = false;
		}
	}

	async function loadIncidents() {
		if (!tenantId || !selectedLine) return;

		incidentsLoading = true;
		incidentsError = null;
		incidents = [];
		const requestId = ++incidentsRequestId;

		const range = rangeOptions.find((item) => item.value === rangeSelection);
		const incidentParams: {
			rangeHours?: number;
			days?: number;
			limit?: number;
			shiftFilter?: string;
		} = {
			limit: 24
		};
		if (includeBothShifts) {
			incidentParams.shiftFilter = 'all';
		}
		if (range?.rangeHours) incidentParams.rangeHours = range.rangeHours;
		if (range?.days) incidentParams.days = range.days;

		try {
			const response = await getShiftIncidents(token, tenantId, selectedLine, incidentParams);
			if (requestId !== incidentsRequestId) return;
			incidents = response.incidents;
		} catch (e) {
			if (requestId !== incidentsRequestId) return;
			incidentsError = e instanceof Error ? e.message : 'Failed to load incidents';
			console.error('Shift incidents error:', e);
		} finally {
			if (requestId === incidentsRequestId) incidentsLoading = false;
		}
	}

	function handleLineChange(line: string) {
		selectedLine = line;
		loadLineData();
		loadIncidents();
	}

	function handleShiftFilterToggle() {
		includeBothShifts = !includeBothShifts;
		loadSnapshot();
		loadLineData();
		loadIncidents();
	}

</script>

<div class="space-y-6">
	<div class="flex flex-col gap-3">
		<div class="flex flex-wrap items-center gap-3">
			{#if shiftLabel}
				<span class="text-xs uppercase tracking-wide px-2 py-1 rounded-full {isDark ? 'bg-gray-800 text-gray-300' : 'bg-gray-100 text-gray-600'}">
					{shiftLabel} shift
				</span>
			{/if}
			<span class="text-xs {isDark ? 'text-gray-400' : 'text-gray-500'}">
				Shift window: {shiftHours}h
			</span>
			<span class="text-xs {isDark ? 'text-gray-400' : 'text-gray-500'}">
				Buckets: {binMinutes} min
			</span>
		</div>
		<div class="flex flex-wrap items-center gap-4">
			<div class="flex items-center gap-2">
				<label class="text-xs {isDark ? 'text-gray-300' : 'text-gray-600'}">Show all shifts</label>
				<button
					class="relative inline-flex h-5 w-10 items-center rounded-full transition-colors {includeBothShifts
						? 'bg-[#5CC9D3]'
						: isDark
							? 'bg-gray-700'
							: 'bg-gray-300'}"
					on:click={handleShiftFilterToggle}
					type="button"
				>
					<span
						class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform {includeBothShifts ? 'translate-x-5' : 'translate-x-1'}"
					></span>
				</button>
			</div>
		</div>
	</div>

	<div class="space-y-3">
		<h2 class="text-lg font-semibold {isDark ? 'text-white' : 'text-gray-900'}">Shift Snapshot</h2>
		{#if snapshotLoading}
			<div class="flex items-center justify-center h-24">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
			</div>
		{:else if snapshotError}
			<div class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
				{snapshotError}
			</div>
		{:else}
			<div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
				{#each snapshotTotals as item}
					<MetricCard label={item.label} value={item.total_units} {isDark} />
				{/each}
			</div>
		{/if}
	</div>

	<div class="space-y-3">
		<div class="flex items-center justify-between">
			<h2 class="text-lg font-semibold {isDark ? 'text-white' : 'text-gray-900'}">Line Comparison</h2>
		</div>
		<div class="flex gap-2 flex-wrap">
			{#each lineOptions as line}
				<button
					class="px-3 py-1.5 text-sm rounded-lg border transition-all {selectedLine === line
						? 'bg-[#5CC9D3] text-white border-[#5CC9D3]'
						: isDark
							? 'bg-gray-800 text-gray-300 border-gray-700 hover:border-[#5CC9D3]'
							: 'bg-white text-gray-700 border-gray-300 hover:border-[#5CC9D3]'}"
					on:click={() => handleLineChange(line)}
				>
					{line}
				</button>
			{/each}
		</div>

		{#if lineLoading}
			<div class="flex items-center justify-center h-24">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
			</div>
		{:else if lineError}
			<div class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
				{lineError}
			</div>
		{:else if throughput}
			<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
				<MetricCard label={`${throughput.left_label} total`} value={throughput.left_total} {isDark} />
				<MetricCard label={`${throughput.right_label} total`} value={throughput.right_total} {isDark} />
				<MetricCard
					label="Difference"
					value={throughput.diff_units}
					chipValue={throughput.diff_percent !== null ? `${throughput.diff_percent.toFixed(1)}%` : null}
					chipColor={throughput.diff_units > 0 ? 'red' : 'neutral'}
					{isDark}
				/>
			</div>
		{/if}

		{#if downTotals.length > 0}
			<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
				{#each downTotals as item}
					<MetricCard label={`${item.label} down`} value={item.down_units} {isDark} />
				{/each}
			</div>
		{/if}

		<div
			class="p-4 rounded-lg border {isDark
				? 'bg-gray-800/50 border-gray-700/50'
				: 'bg-white border-gray-200'}"
		>
			<MultiLineChart
				title="Cumulative Units"
				subtitle={chartSubtitle}
				series={chartSeries}
				{isDark}
				height={260}
				xLabelMode="auto"
			/>
		</div>
	</div>

	<div class="space-y-3">
		<div class="flex flex-wrap items-center justify-between gap-3">
			<h3 class="text-sm font-semibold {isDark ? 'text-white' : 'text-gray-900'}">Recent Incidents</h3>
		</div>
		<ShiftIncidentsList
			incidents={incidents}
			{isDark}
			loading={incidentsLoading}
			error={incidentsError}
		/>
	</div>
</div>
