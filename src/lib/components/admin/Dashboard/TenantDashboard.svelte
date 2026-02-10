<script lang="ts">
	import { onMount } from 'svelte';

	import MetricCard from './Cards/MetricCard.svelte';
	import DPMOCard from './Cards/DPMOCard.svelte';
	import ToggleBar from './Toggle/ToggleBar.svelte';
	import LineChart from './Charts/LineChart.svelte';
	import HistogramChart from './Charts/HistogramChart.svelte';
	import IncidentsList from './Incidents/IncidentsList.svelte';
	import ShiftDashboard from './ShiftDashboard.svelte';
	import { shiftRangeOptions } from './shiftRangeOptions';
	import CaseInspectionDashboard from './CaseInspectionDashboard.svelte';
	import SidewallDashboard from './SidewallDashboard.svelte';
	import LehrInspectionDashboard from './LehrInspectionDashboard.svelte';
	import ScaleWeightDashboard from './ScaleWeightDashboard.svelte';
	import FinalCheckDashboard from './FinalCheckDashboard.svelte';
	import InsightsPanel from './InsightsPanel.svelte';
	import { defaultRangeOptions, sidewallRangeOptions } from './timeRangeOptions';

	import {
		getAvailableDashboards,
		getTenantConfig,
		getOverview,
		getLineMetrics,
		getTimeSeries,
		getOrientation,
		getIncidents,
		getUVBCIntensity,
		getPartialRings,
		getSystemHealth,
		type TenantDashboardConfig,
		type OverviewMetric,
		type LineMetrics as LineMetricsType,
		type TimeSeriesPoint,
		type OrientationBin,
		type Incident,
		type IntensityStats,
		type PartialRingData,
		type DeviceHealth
	} from '$lib/apis/dashboard';

	import {
		selectedTenantId,
		selectedLine,
		selectedSystem,
		selectedSecondaryOption,
		dateRange,
		chartColors
	} from '$lib/stores/dashboard';
	import { user } from '$lib/stores';

	// Props
	export let token: string;

	const DPMO_HELP =
		'Defects per million opportunities: (defects ÷ total units) × 1,000,000 over the selected time range.';

	const METRIC_HELP: Record<string, Record<string, string>> = {
		uvbc: {
			total: 'Total units for UVBC is SUM(uvring) over the selected time range (matches Grafana "UVRing").',
			down: 'UV Down defects: SUM(uvdown) over the selected time range.',
			edge: 'Edge defects: SUM(edge) over the selected time range.',
			no_coats: 'No Coating defects: SUM(nocoating) over the selected time range.',
			partials: 'Partial Coverage defects: SUM(uvpartial) over the selected time range.',
			blobs: 'Blob defects: SUM(blob) over the selected time range.',
			avg_fps: 'Average FPS: AVG(nn_fps) over the selected time range.'
		},
		washer: {
			total:
				'Total units for Washer uses SUM(can) when available; if can is NULL, it estimates throughput from nn_fps assuming ~10-minute totals intervals.',
			down: 'Down defects: SUM(down) over the selected time range.',
			inverted: 'Inverted defects: SUM(inverted) over the selected time range.',
			avg_fps: 'Average FPS: AVG(nn_fps) over the selected time range.'
		}
	};
	const SYSTEM_LABELS: Record<string, string> = {
		finalcheck: 'FinalCheck'
	};

	const formatSystemLabel = (system: string) => {
		const key = (system || '').toLowerCase();
		return SYSTEM_LABELS[key] || system.toUpperCase();
	};

	// Local state
	let isDark = false;
	let loading = true;
	let error: string | null = null;
	let overviewLoading = false;
	let overviewError: string | null = null;
	let lineLoading = false;
	let lineError: string | null = null;
	let lineRequestId = 0;
	let selectedSystemLabel = '';
	let isFinalCheckSystem = false;
	let dashboardView = 'Dashboard';
	let baseSystemsForLine: string[] = [];

	const dashboardViewOptions = ['Dashboard', 'Insights'];

	let availableTenants: { id: string; display_name: string; tenant_group_name?: string | null }[] = [];
	let selectedTenantGroup = 'all';
	let tenantConfig: TenantDashboardConfig | null = null;
	let derivedLineSystems: Record<string, string[]> = {};
	let lineOptions: string[] = [];
	let overviewMetrics: OverviewMetric[] = [];
	let lineMetrics: LineMetricsType | null = null;
	let timeSeriesData: TimeSeriesPoint[] = [];
	let orientationData: OrientationBin[] = [];
	let orientationLoading = false;
	let orientationError: string | null = null;
	let incidentsData: Incident[] = [];
	let incidentsLoading = false;
	let incidentsError: string | null = null;
	let intensityData: any[] = [];
	let partialRingsData: PartialRingData[] = [];
	let coatingLoading = false;
	let coatingError: string | null = null;
	let systemHealthData: DeviceHealth[] = [];
	let systemHealthLoading = false;
	let systemHealthError: string | null = null;
	let systemHealthTimestamp: string = '';
	let shiftSelection = 'all';
	let shiftTenantId = '';
	let shiftRangeSelection = 'shift';
	let shiftRangeTenantId = '';
	let rangeSelection = '7d';
	let rangeTenantId = '';

	function syncTenantGroup(
		tenants: { id: string; display_name: string; tenant_group_name?: string | null }[]
	) {
		if ($user?.role !== 'admin') {
			selectedTenantGroup = 'all';
			return;
		}
		const groups = new Set(tenants.map((tenant) => tenant.tenant_group_name).filter(Boolean));
		if (groups.size === 0) {
			selectedTenantGroup = 'all';
			return;
		}
		if (
			selectedTenantGroup !== 'all' &&
			!tenants.some((tenant) => tenant.tenant_group_name === selectedTenantGroup)
		) {
			selectedTenantGroup = 'all';
		}
	}

	function getRangeParams(selection?: string) {
		const option = activeRangeOptions.find((item) => item.value === (selection ?? rangeSelection));
		return {
			rangeHours: option?.rangeHours,
			days: option?.days
		};
	}

	function deriveLineSystems(config?: TenantDashboardConfig | null) {
		const factories = config?.factories;
		if (!factories) {
			return {
				lineOptions: config?.available_lines || [],
				lineSystems: config?.line_systems || {}
			};
		}
		const lineOptions: string[] = [];
		const lineSystems: Record<string, string[]> = {};
		Object.values(factories).forEach((factory) => {
			Object.values(factory.lines || {}).forEach((line) => {
				if (!line?.id) return;
				lineOptions.push(line.id);
				lineSystems[line.id] = Object.keys(line.solutions || {});
			});
		});
		return {
			lineOptions: lineOptions.length ? lineOptions : config?.available_lines || [],
			lineSystems: Object.keys(lineSystems).length ? lineSystems : config?.line_systems || {}
		};
	}

	// Computed
	let activeRangeOptions = defaultRangeOptions;
	$: {
		const configuredRanges = tenantConfig?.time_ranges;
		const fallbackOptions = isSidewallDashboard ? sidewallRangeOptions : defaultRangeOptions;
		if (!configuredRanges || configuredRanges.length === 0) {
			activeRangeOptions = fallbackOptions;
		} else {
			const optionMap = new Map(defaultRangeOptions.map((option) => [option.value, option]));
			activeRangeOptions = configuredRanges
				.map((value) => optionMap.get(value))
				.filter((option) => option !== undefined) as typeof defaultRangeOptions;
		}
	}
	$: currentRangeOption = activeRangeOptions.find((option) => option.value === rangeSelection);
	$: currentRangeLabel = currentRangeOption?.label || 'Last 7 days';
	$: currentRangeDays = currentRangeOption?.days ?? 1;
	$: currentRangeHours = currentRangeOption?.rangeHours;
	$: ({ lineOptions, lineSystems: derivedLineSystems } = deriveLineSystems(tenantConfig));
	$: finalcheckLineId = tenantConfig?.finalcheck_line_id || 'CX';
	$: hasFinalCheck = (tenantConfig?.available_systems || []).includes('finalcheck');
	$: baseSystemsForLine =
		$selectedLine && derivedLineSystems?.[$selectedLine]
			? derivedLineSystems[$selectedLine]
			: tenantConfig?.available_systems || [];
	$: supportedSystemsForLine =
		hasFinalCheck && !baseSystemsForLine.includes('finalcheck')
			? [...baseSystemsForLine, 'finalcheck']
			: baseSystemsForLine;
	$: tenantGroups = Array.from(
		new Set(availableTenants.map((tenant) => tenant.tenant_group_name).filter(Boolean))
	) as string[];
	$: visibleTenants =
		$user?.role === 'admin' && selectedTenantGroup !== 'all'
			? availableTenants.filter((tenant) => tenant.tenant_group_name === selectedTenantGroup)
			: availableTenants;
	$: systemOptions = supportedSystemsForLine.map((s) => formatSystemLabel(s));
	$: selectedSystemLabel = formatSystemLabel($selectedSystem);
	$: secondaryOptions = ['Metrics', 'Orientation', 'Coating', 'System'];
	$: isShiftDashboard = tenantConfig?.dashboard_type === 'shift';
	$: isCaseInspectionDashboard = tenantConfig?.dashboard_type === 'case_inspection';
	$: isSidewallDashboard = tenantConfig?.dashboard_type === 'sidewall';
	$: isLehrDashboard = tenantConfig?.dashboard_type === 'lehr_inspection';
	$: isScaleWeightDashboard = tenantConfig?.dashboard_type === 'scale_weight';
	$: isFinalCheckSystem = $selectedSystem.toLowerCase() === 'finalcheck';
	$: insightsForView =
		tenantConfig?.insights_by_system && tenantConfig?.dashboard_type === 'quality'
			? tenantConfig.insights_by_system[$selectedSystem.toLowerCase()] || tenantConfig?.insights || []
			: tenantConfig?.insights || [];
	$: shiftOptions = tenantConfig?.shift_options || [];
	$: hasShiftFilter = shiftOptions.length > 0;
	$: if (hasShiftFilter && $selectedTenantId !== shiftTenantId) {
		shiftSelection = tenantConfig?.shift_default || shiftOptions[0]?.id || 'all';
		shiftTenantId = $selectedTenantId;
	} else if (!hasShiftFilter && $selectedTenantId !== shiftTenantId) {
		shiftSelection = 'all';
		shiftTenantId = $selectedTenantId;
	}

	$: if (visibleTenants.length > 0 && !visibleTenants.find((tenant) => tenant.id === $selectedTenantId)) {
		selectedTenantId.set(visibleTenants[0].id);
	}
	$: if (activeRangeOptions.length > 0 && !activeRangeOptions.find((option) => option.value === rangeSelection)) {
		rangeSelection = activeRangeOptions[0].value;
	}
	$: if (
		!isShiftDashboard &&
		!isCaseInspectionDashboard &&
		!isSidewallDashboard &&
		!isScaleWeightDashboard &&
		!isLehrDashboard &&
		lineOptions.length > 0 &&
		$selectedLine &&
		!lineOptions.includes($selectedLine)
	) {
		selectedLine.set(lineOptions[0]);
	}
	$: if (supportedSystemsForLine.length > 0 && !supportedSystemsForLine.includes($selectedSystem)) {
		selectedSystem.set(supportedSystemsForLine[0]);
	}
	$: if (isShiftDashboard && $selectedTenantId !== shiftRangeTenantId) {
		shiftRangeSelection = 'shift';
		shiftRangeTenantId = $selectedTenantId;
	}

	// Theme detection
	onMount(() => {
		isDark = document.documentElement.classList.contains('dark');

		const observer = new MutationObserver(() => {
			isDark = document.documentElement.classList.contains('dark');
		});

		observer.observe(document.documentElement, {
			attributes: true,
			attributeFilter: ['class']
		});

		loadDashboard();

		return () => observer.disconnect();
	});

	async function loadDashboard() {
		loading = true;
		error = null;
		dashboardView = 'Dashboard';

		try {
			// Load available tenants
			availableTenants = await getAvailableDashboards(token);
			syncTenantGroup(availableTenants);

			if (availableTenants.length === 0) {
				throw new Error('No dashboards are available for your account');
			}

			const availableIds = new Set(availableTenants.map((t) => t.id));
			let tenantId = $selectedTenantId;
			if (!tenantId || !availableIds.has(tenantId)) {
				tenantId = availableTenants[0].id;
				selectedTenantId.set(tenantId);
			}

			// Load tenant config
			if (tenantId) {
				tenantConfig = await getTenantConfig(token, tenantId);
				const finalLine = tenantConfig?.finalcheck_line_id || 'CX';
				if ($selectedSystem.toLowerCase() === 'finalcheck' && finalLine) {
					if ($selectedLine !== finalLine) {
						selectedLine.set(finalLine);
					}
				}

				if (tenantConfig.shift_options && tenantConfig.shift_options.length > 0) {
					shiftSelection = tenantConfig.shift_default || tenantConfig.shift_options[0].id || 'all';
				} else {
					shiftSelection = 'all';
				}
				shiftTenantId = tenantId;
				if (tenantId !== rangeTenantId) {
					const preferredRanges = tenantConfig.time_ranges || [];
					if (tenantConfig.dashboard_type === 'sidewall') {
						rangeSelection = preferredRanges.includes('12h') ? '12h' : preferredRanges[0] || '12h';
					} else if (tenantConfig.dashboard_type === 'lehr_inspection') {
						rangeSelection = preferredRanges.includes('6h') ? '6h' : preferredRanges[0] || '6h';
					} else if (tenantConfig.dashboard_type === 'scale_weight') {
						rangeSelection = preferredRanges.includes('6h') ? '6h' : preferredRanges[0] || '6h';
					} else {
						rangeSelection = preferredRanges[0] || '7d';
					}
					rangeTenantId = tenantId;
				}

				if (tenantConfig.dashboard_type === 'shift') {
					selectedLine.set(null);
					selectedSecondaryOption.set('metrics');
					return;
				}

				if (tenantConfig.dashboard_type === 'case_inspection') {
					selectedLine.set(null);
					selectedSecondaryOption.set('metrics');
					return;
				}

				if (tenantConfig.dashboard_type === 'sidewall') {
					selectedLine.set(null);
					selectedSecondaryOption.set('metrics');
					return;
				}

				if (tenantConfig.dashboard_type === 'scale_weight') {
					selectedLine.set(null);
					selectedSecondaryOption.set('metrics');
					return;
				}

				// Set default line if not set
				if (!$selectedLine && lineOptions.length > 0) {
					selectedLine.set(lineOptions[0]);
				}

				// Ensure selected system is valid for the selected line
				const lineId = $selectedLine;
				const supportedSystems =
					(lineId && tenantConfig.line_systems?.[lineId]) || tenantConfig.available_systems || [];
				const desiredSystem = $selectedSystem.toLowerCase();
				if (!supportedSystems.includes(desiredSystem)) {
					selectedSystem.set(supportedSystems[0] || tenantConfig.available_systems[0] || 'uvbc');
				}

				// Load overview
				await loadOverview(undefined, tenantId);

				// Load line metrics and incidents if line selected
				if ($selectedLine) {
					await loadLineData({ tenantId });
					await loadIncidentsData({ tenantId });
				}
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load dashboard';
			console.error('Dashboard load error:', e);
		} finally {
			loading = false;
		}
	}

	async function loadOverview(options: {
		tenantId?: string;
		days?: number;
		rangeHours?: number;
		shiftFilter?: string;
	} = {}) {
		const tenantId = options.tenantId ?? $selectedTenantId;
		const selection = getRangeParams();
		const rangeHours = options.rangeHours ?? selection.rangeHours;
		const days = options.days ?? selection.days ?? currentRangeDays;
		const shiftFilter = options.shiftFilter ?? (hasShiftFilter ? shiftSelection : undefined);
		overviewLoading = true;
		overviewError = null;
		try {
			const response = await getOverview(token, tenantId, days, {
				shiftFilter,
				rangeHours
			});
			overviewMetrics = response.metrics;
		} catch (e) {
			overviewError = e instanceof Error ? e.message : 'Failed to load overview';
			console.error('Failed to load overview:', e);
		} finally {
			overviewLoading = false;
		}
	}

	async function loadLineData(options: {
		tenantId?: string;
		lineId?: string;
		system?: string;
		days?: number;
		rangeHours?: number;
		shiftFilter?: string;
	} = {}) {
		const tenantId = options.tenantId ?? $selectedTenantId;
		const lineId = options.lineId ?? $selectedLine;
		const system = (options.system ?? $selectedSystem).toLowerCase();
		const selection = getRangeParams();
		const rangeHours = options.rangeHours ?? selection.rangeHours;
		const days = options.days ?? selection.days ?? currentRangeDays;
		const shiftFilter = options.shiftFilter ?? (hasShiftFilter ? shiftSelection : undefined);

		if (!tenantId || !lineId) return;
		if (system === 'finalcheck') {
			lineLoading = false;
			lineError = null;
			lineMetrics = null;
			timeSeriesData = [];
			return;
		}

		const requestId = ++lineRequestId;
		lineLoading = true;
		lineError = null;
		lineMetrics = null;
		timeSeriesData = [];

		try {
			const [metrics, ts] = await Promise.all([
				getLineMetrics(token, tenantId, lineId, system, days, { shiftFilter, rangeHours }),
				getTimeSeries(token, tenantId, lineId, 'down', system, days, { shiftFilter, rangeHours })
			]);

			if (requestId !== lineRequestId) return;

			lineMetrics = metrics;
			timeSeriesData = ts.data;
		} catch (e) {
			if (requestId !== lineRequestId) return;
			lineError = e instanceof Error ? e.message : 'Failed to load line data';
			console.error('Failed to load line data:', e);
		} finally {
			if (requestId === lineRequestId) lineLoading = false;
		}
	}

	async function loadOrientationData(options: {
		tenantId?: string;
		lineId?: string;
		system?: string;
		days?: number;
		rangeHours?: number;
		shiftFilter?: string;
	} = {}) {
		const tenantId = options.tenantId ?? $selectedTenantId;
		const lineId = options.lineId ?? $selectedLine;
		const system = (options.system ?? $selectedSystem).toLowerCase();
		const selection = getRangeParams();
		const rangeHours = options.rangeHours ?? selection.rangeHours;
		const days = options.days ?? selection.days ?? currentRangeDays;
		const shiftFilter = options.shiftFilter ?? (hasShiftFilter ? shiftSelection : undefined);

		if (!tenantId || !lineId) return;
		if (system === 'finalcheck') {
			orientationData = [];
			return;
		}

		orientationLoading = true;
		orientationError = null;
		orientationData = [];

		try {
			const response = await getOrientation(token, tenantId, lineId, {
				system,
				defectType: system === 'washer' ? 'down' : 'uvdown',
				days,
				binSize: 100,
				shiftFilter,
				rangeHours
			});
			orientationData = response.data;
		} catch (e) {
			orientationError = e instanceof Error ? e.message : 'Failed to load orientation data';
			console.error('Failed to load orientation data:', e);
		} finally {
			orientationLoading = false;
		}
	}

	async function loadIncidentsData(options: {
		tenantId?: string;
		lineId?: string;
		system?: string;
		days?: number;
		rangeHours?: number;
		shiftFilter?: string;
	} = {}) {
		const tenantId = options.tenantId ?? $selectedTenantId;
		const lineId = options.lineId ?? $selectedLine;
		const system = (options.system ?? $selectedSystem).toLowerCase();
		const selection = getRangeParams();
		const rangeHours = options.rangeHours ?? selection.rangeHours;
		const days = options.days ?? selection.days ?? currentRangeDays;
		const shiftFilter = options.shiftFilter ?? (hasShiftFilter ? shiftSelection : undefined);

		if (!tenantId || !lineId) return;
		if (system === 'finalcheck') {
			incidentsLoading = false;
			incidentsError = null;
			incidentsData = [];
			return;
		}

		incidentsLoading = true;
		incidentsError = null;
		incidentsData = [];

		try {
			const response = await getIncidents(token, tenantId, lineId, {
				system,
				limit: 10,
				largeOnly: false,
				days,
				shiftFilter,
				rangeHours
			});
			incidentsData = response.incidents;
		} catch (e) {
			incidentsError = e instanceof Error ? e.message : 'Failed to load incidents';
			console.error('Failed to load incidents:', e);
		} finally {
			incidentsLoading = false;
		}
	}

	async function loadCoatingData(options: {
		tenantId?: string;
		lineId?: string;
		days?: number;
		rangeHours?: number;
		shiftFilter?: string;
	} = {}) {
		const tenantId = options.tenantId ?? $selectedTenantId;
		const lineId = options.lineId ?? $selectedLine;
		const selection = getRangeParams();
		const rangeHours = options.rangeHours ?? selection.rangeHours;
		const days = options.days ?? selection.days ?? currentRangeDays;
		const shiftFilter = options.shiftFilter ?? (hasShiftFilter ? shiftSelection : undefined);

		// Coating only applies to UVBC system
		if (!tenantId || !lineId || $selectedSystem.toLowerCase() !== 'uvbc') {
			intensityData = [];
			partialRingsData = [];
			return;
		}

		coatingLoading = true;
		coatingError = null;

		try {
			const [intensityResponse, partialsResponse] = await Promise.all([
				getUVBCIntensity(token, tenantId, lineId, days, { shiftFilter, rangeHours }),
				getPartialRings(token, tenantId, lineId, days, { shiftFilter, rangeHours })
			]);
			intensityData = intensityResponse.data;
			partialRingsData = partialsResponse.data;
		} catch (e) {
			coatingError = e instanceof Error ? e.message : 'Failed to load coating data';
			console.error('Failed to load coating data:', e);
		} finally {
			coatingLoading = false;
		}
	}

	async function loadSystemHealthData(options: { tenantId?: string } = {}) {
		const tenantId = options.tenantId ?? $selectedTenantId;

		if (!tenantId) {
			systemHealthData = [];
			return;
		}

		systemHealthLoading = true;
		systemHealthError = null;

		try {
			const response = await getSystemHealth(token, tenantId);
			systemHealthData = response.devices;
			systemHealthTimestamp = response.timestamp;
		} catch (e) {
			systemHealthError = e instanceof Error ? e.message : 'Failed to load system health';
			console.error('Failed to load system health:', e);
		} finally {
			systemHealthLoading = false;
		}
	}

	function handleTenantGroupChange(groupName: string) {
		selectedTenantGroup = groupName;
		dashboardView = 'Dashboard';
		if (groupName === 'all') {
			return;
		}
		const firstInGroup = availableTenants.find((tenant) => tenant.tenant_group_name === groupName);
		if (firstInGroup) {
			selectedTenantId.set(firstInGroup.id);
			selectedLine.set(null);
			loadDashboard();
		}
	}

	function handleTenantChange(tenantId: string) {
		selectedTenantId.set(tenantId);
		dashboardView = 'Dashboard';
		selectedLine.set(null);
		loadDashboard();
	}

	function handleDashboardViewChange(view: string) {
		dashboardView = view;
	}

	async function handleLineChange(line: string) {
		selectedLine.set(line);

		// Ensure selected system is valid for this line
		const lineSystems = tenantConfig?.line_systems?.[line] || tenantConfig?.available_systems || [];
		const fallbackSystems = lineSystems.filter((sys) => sys !== 'finalcheck');
		if ($selectedSystem.toLowerCase() === 'finalcheck' && line !== finalcheckLineId) {
			if (fallbackSystems.length > 0) {
				selectedSystem.set(fallbackSystems[0]);
			}
		} else if (lineSystems.length > 0 && !lineSystems.includes($selectedSystem.toLowerCase())) {
			selectedSystem.set(lineSystems[0]);
		}

		if ($selectedSystem.toLowerCase() === 'finalcheck') {
			return;
		}
		await loadLineData({ lineId: line });
		await loadIncidentsData({ lineId: line });
	}

	async function handleSystemChange(system: string) {
		const normalized = system.toLowerCase();
		selectedSystem.set(normalized);
		if (normalized === 'finalcheck') {
			if (finalcheckLineId && $selectedLine !== finalcheckLineId) {
				selectedLine.set(finalcheckLineId);
			}
			selectedSecondaryOption.set('metrics');
			return;
		}
		await loadLineData({ system: normalized });
		await loadIncidentsData({ system: normalized });
	}

	async function handleSecondaryChange(option: string) {
		if ($selectedSystem.toLowerCase() === 'finalcheck') {
			return;
		}
		const lowerOption = option.toLowerCase();
		selectedSecondaryOption.set(lowerOption);

		if (lowerOption === 'orientation') {
			await loadOrientationData();
		} else if (lowerOption === 'coating') {
			await loadCoatingData();
		} else if (lowerOption === 'system') {
			await loadSystemHealthData();
		}
	}

	function handleShiftChange(value: string) {
		shiftSelection = value;
		loadOverview({ shiftFilter: value });
		if ($selectedSystem.toLowerCase() !== 'finalcheck') {
			loadLineData({ shiftFilter: value });
			loadIncidentsData({ shiftFilter: value });
			if ($selectedSecondaryOption === 'orientation') {
				loadOrientationData({ shiftFilter: value });
			} else if ($selectedSecondaryOption === 'coating') {
				loadCoatingData({ shiftFilter: value });
			}
		}
	}

	function handleRangeChange(value: string) {
		rangeSelection = value;
		const selection = getRangeParams(value);
		const days = selection.days ?? 1;
		dateRange.update((d) => ({
			...d,
			days,
			start: new Date(Date.now() - days * 24 * 60 * 60 * 1000)
		}));
		loadOverview({ days: selection.days, rangeHours: selection.rangeHours });
		if ($selectedSystem.toLowerCase() !== 'finalcheck') {
			loadLineData({ days: selection.days, rangeHours: selection.rangeHours });
			loadIncidentsData({ days: selection.days, rangeHours: selection.rangeHours });
			if ($selectedSecondaryOption === 'orientation') {
				loadOrientationData({ days: selection.days, rangeHours: selection.rangeHours });
			} else if ($selectedSecondaryOption === 'coating') {
				loadCoatingData({ days: selection.days, rangeHours: selection.rangeHours });
			}
		}
	}
</script>

<div class="w-full h-full overflow-y-auto {isDark ? 'bg-gray-900' : 'bg-gray-50'}">
	<div class="p-6 space-y-3">
		<!-- Header -->
		<div class="flex flex-col gap-1">
			{#if $user?.role === 'admin' && tenantGroups.length > 0}
				<div class="w-full h-12 flex items-center gap-2 px-8 overflow-x-auto flex-nowrap {isDark ? 'bg-gray-800' : 'bg-gray-50'}">
					<button
						class="px-2.5 py-1 text-xs font-medium rounded-lg shadow-lg flex-shrink-0 transition-colors {selectedTenantGroup === 'all'
							? isDark
								? 'bg-gray-600 text-white'
								: 'bg-gray-700 text-white'
							: isDark
								? 'bg-gray-800 text-gray-300 hover:bg-gray-700'
								: 'bg-gray-100 text-gray-700 hover:bg-gray-200'}"
						on:click={() => handleTenantGroupChange('all')}
					>
						All
					</button>
					{#each tenantGroups as groupName}
						<button
							class="px-2.5 py-1 text-xs font-medium rounded-lg shadow-lg flex-shrink-0 transition-colors {selectedTenantGroup === groupName
								? isDark
									? 'bg-gray-600 text-white'
									: 'bg-gray-700 text-white'
								: isDark
									? 'bg-gray-800 text-gray-300 hover:bg-gray-700'
									: 'bg-gray-100 text-gray-700 hover:bg-gray-200'}"
							on:click={() => handleTenantGroupChange(groupName)}
						>
							{groupName}
						</button>
					{/each}
				</div>
			{/if}

			<!-- Dashboard toggle bar -->
			{#if ($user?.role === 'admin' && visibleTenants.length > 0) || visibleTenants.length > 1}
				<div class="w-full h-12 flex items-center gap-2 px-8 overflow-x-auto flex-nowrap {isDark ? 'bg-gray-800' : 'bg-gray-50'}">
					{#each visibleTenants as tenant}
						<button
							class="px-2.5 py-1 text-xs font-medium rounded-lg shadow-lg flex-shrink-0 transition-colors {$selectedTenantId === tenant.id
								? isDark
									? 'bg-gray-600 text-white'
									: 'bg-gray-700 text-white'
								: isDark
									? 'bg-gray-800 text-gray-300 hover:bg-gray-700'
									: 'bg-gray-100 text-gray-700 hover:bg-gray-200'}"
							on:click={() => handleTenantChange(tenant.id)}
						>
							{tenant.display_name}
						</button>
					{/each}
				</div>
			{/if}

			<div class="flex items-center justify-between">
				<h1 class="text-2xl font-bold {isDark ? 'text-white' : 'text-gray-900'}">
					{tenantConfig?.display_name || 'Quality Dashboard'}
				</h1>
				{#if isShiftDashboard}
					<div class="flex items-center gap-2">
						<select
							class="px-3 py-1.5 text-sm rounded-lg border {isDark
								? 'bg-gray-800 border-gray-700 text-white'
								: 'bg-white border-gray-300 text-gray-900'}"
							value={shiftRangeSelection}
							on:change={(e) => (shiftRangeSelection = e.currentTarget.value)}
							aria-label="Time range"
						>
							{#each shiftRangeOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
					</div>
				{:else}
					<div class="flex items-center gap-2">
						{#if hasShiftFilter}
							<select
								class="px-3 py-1.5 text-sm rounded-lg border {isDark
									? 'bg-gray-800 border-gray-700 text-white'
									: 'bg-white border-gray-300 text-gray-900'}"
								value={shiftSelection}
								on:change={(e) => handleShiftChange(e.currentTarget.value)}
								aria-label="Shift filter"
							>
								{#each shiftOptions as option}
									<option value={option.id}>{option.label}</option>
								{/each}
							</select>
						{/if}
						<select
							class="px-3 py-1.5 text-sm rounded-lg border {isDark
								? 'bg-gray-800 border-gray-700 text-white'
								: 'bg-white border-gray-300 text-gray-900'}"
							value={rangeSelection}
							on:change={(e) => handleRangeChange(e.currentTarget.value)}
						>
							{#each activeRangeOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
					</div>
				{/if}
			</div>
			<div class="flex items-center justify-end">
				<ToggleBar
					options={dashboardViewOptions}
					selected={dashboardView}
					onSelect={handleDashboardViewChange}
					{isDark}
					size="sm"
				/>
			</div>
		</div>

		{#if loading}
			<div class="flex items-center justify-center h-64">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#5CC9D3]"></div>
			</div>
		{:else if error}
			<div
				class="p-4 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}"
			>
				{error}
			</div>
		{:else}
			{#if dashboardView === 'Insights'}
				<InsightsPanel insights={insightsForView} {isDark} />
			{:else if isShiftDashboard}
				<ShiftDashboard
					token={token}
					tenantId={$selectedTenantId}
					{tenantConfig}
					{isDark}
					rangeOptions={shiftRangeOptions}
					bind:rangeSelection={shiftRangeSelection}
				/>
			{:else if isCaseInspectionDashboard}
				<CaseInspectionDashboard
					token={token}
					tenantId={$selectedTenantId}
					{tenantConfig}
					rangeLabel={currentRangeLabel}
					rangeParams={{ days: currentRangeOption?.days, rangeHours: currentRangeOption?.rangeHours }}
					{isDark}
				/>
			{:else if isSidewallDashboard}
				<SidewallDashboard
					token={token}
					tenantId={$selectedTenantId}
					{tenantConfig}
					rangeLabel={currentRangeLabel}
					rangeParams={{ days: currentRangeOption?.days, rangeHours: currentRangeOption?.rangeHours }}
					{isDark}
				/>
			{:else if isLehrDashboard}
				<LehrInspectionDashboard
					token={token}
					tenantId={$selectedTenantId}
					{tenantConfig}
					rangeLabel={currentRangeLabel}
					rangeParams={{ days: currentRangeOption?.days, rangeHours: currentRangeOption?.rangeHours }}
					{isDark}
				/>
			{:else if isScaleWeightDashboard}
				<ScaleWeightDashboard
					token={token}
					tenantId={$selectedTenantId}
					{tenantConfig}
					rangeLabel={currentRangeLabel}
					rangeParams={{ days: currentRangeOption?.days, rangeHours: currentRangeOption?.rangeHours }}
					{isDark}
				/>
			{:else}
				<!-- Overview Section -->
				<div class="space-y-4">
					<h2 class="text-lg font-semibold {isDark ? 'text-white' : 'text-gray-900'}">
						Overview
					</h2>
					{#if overviewLoading}
						<div class="flex items-center justify-center h-24">
							<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
						</div>
					{:else if overviewError}
						<div
							class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}"
						>
							{overviewError}
						</div>
					{:else}
						<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
								{#each overviewMetrics as metric}
									<DPMOCard
										line={metric.line || metric.device_id || 'Unknown'}
										system={metric.system}
										dpmo={metric.dpmo}
										totalUnits={metric.total_units}
										changePercent={metric.change_percent}
										isEstimated={metric.dpmo_estimated ?? false}
										historicalDpmo={metric.historical_dpmo}
										dpmoHelpText={DPMO_HELP}
										{isDark}
										onClick={() => metric.line && handleLineChange(metric.line)}
									/>
								{/each}
						</div>
					{/if}
				</div>

				<!-- Line Details Section -->
				{#if $selectedLine && tenantConfig}
					<div class="space-y-4">
						<div class="flex items-center justify-between">
							<h2 class="text-lg font-semibold {isDark ? 'text-white' : 'text-gray-900'}">
								Line Details: {$selectedLine}
							</h2>
						</div>

						<!-- System Toggle -->
						{#if systemOptions.length > 1}
							<ToggleBar
								options={systemOptions}
								selected={selectedSystemLabel}
								onSelect={handleSystemChange}
								{isDark}
							/>
						{/if}

						<!-- Line Selector -->
						<div class="flex gap-2 flex-wrap">
							{#each lineOptions as line}
								<button
									class="px-3 py-1.5 text-sm rounded-lg border transition-all {$selectedLine === line
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

						{#if isFinalCheckSystem}
							<FinalCheckDashboard
								token={token}
								tenantId={$selectedTenantId}
								lineId={$selectedLine}
								rangeLabel={currentRangeLabel}
								rangeParams={{ days: currentRangeOption?.days, rangeHours: currentRangeOption?.rangeHours }}
								{isDark}
							/>
						{:else}
							<!-- Secondary Options -->
							<ToggleBar
								options={secondaryOptions}
								selected={$selectedSecondaryOption.charAt(0).toUpperCase() + $selectedSecondaryOption.slice(1)}
								onSelect={handleSecondaryChange}
								{isDark}
								size="sm"
							/>

							<!-- Content based on secondary option -->
							{#if $selectedSecondaryOption === 'metrics'}
								<!-- Metrics View -->
								{#if lineLoading}
									<div class="flex items-center justify-center h-24">
										<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
									</div>
								{:else if lineError}
									<div
										class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}"
									>
										{lineError}
									</div>
								{:else if lineMetrics}
									{#if $selectedSystem.toLowerCase() === 'washer'}
										<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
											<MetricCard
												label="Total Units"
												value={lineMetrics.metrics?.total ?? 0}
												helpText={METRIC_HELP.washer.total}
												{isDark}
											/>
											<MetricCard
												label="Down"
												value={lineMetrics.metrics?.down ?? 0}
												helpText={METRIC_HELP.washer.down}
												{isDark}
											/>
											<MetricCard
												label="Inverted"
												value={lineMetrics.metrics?.inverted ?? 0}
												helpText={METRIC_HELP.washer.inverted}
												{isDark}
											/>
											<MetricCard label="Avg FPS" value={lineMetrics.avg_fps} helpText={METRIC_HELP.washer.avg_fps} {isDark} />
										</div>
									{:else}
										<div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-4">
											<MetricCard
												label="Total Units (UV Ring)"
												value={lineMetrics.metrics?.total ?? 0}
												helpText={METRIC_HELP.uvbc.total}
												{isDark}
											/>
											<MetricCard
												label="UV Down"
												value={lineMetrics.metrics?.down ?? 0}
												chipValue={(lineMetrics.metrics?.down ?? 0) > 0 && (lineMetrics.metrics?.total ?? 0) > 0
													? `${(((lineMetrics.metrics?.down ?? 0) / (lineMetrics.metrics?.total ?? 0)) * 100).toFixed(2)}%`
													: null}
												chipColor="red"
												helpText={METRIC_HELP.uvbc.down}
												{isDark}
											/>
											<MetricCard
												label="Edge"
												value={lineMetrics.metrics?.edge ?? 0}
												helpText={METRIC_HELP.uvbc.edge}
												{isDark}
											/>
											<MetricCard
												label="No Coating"
												value={lineMetrics.metrics?.no_coats ?? 0}
												helpText={METRIC_HELP.uvbc.no_coats}
												{isDark}
											/>
											<MetricCard
												label="Partials"
												value={lineMetrics.metrics?.partials ?? 0}
												helpText={METRIC_HELP.uvbc.partials}
												{isDark}
											/>
											<MetricCard
												label="Blobs"
												value={lineMetrics.metrics?.blobs ?? 0}
												helpText={METRIC_HELP.uvbc.blobs}
												{isDark}
											/>
											<MetricCard label="Avg FPS" value={lineMetrics.avg_fps} helpText={METRIC_HELP.uvbc.avg_fps} {isDark} />
										</div>
									{/if}

									<!-- Chart Section -->
									<div
										class="p-4 rounded-lg border {isDark
											? 'bg-gray-800/50 border-gray-700/50'
											: 'bg-white border-gray-200'}"
									>
										<LineChart
											title={$selectedSystem.toLowerCase() === 'washer' ? 'Down Trend' : 'UV Down Trend'}
											subtitle={currentRangeLabel}
											data={timeSeriesData}
											color={chartColors.primary}
											{isDark}
											height={250}
										/>
									</div>
								{/if}

							{:else if $selectedSecondaryOption === 'orientation'}
								<!-- Orientation View -->
								{#if orientationLoading}
									<div class="flex items-center justify-center h-24">
										<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
									</div>
								{:else if orientationError}
									<div
										class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}"
									>
										{orientationError}
									</div>
								{:else}
									<div
										class="p-4 rounded-lg border {isDark
											? 'bg-gray-800/50 border-gray-700/50'
											: 'bg-white border-gray-200'}"
									>
										<HistogramChart
											title="Defect Location Distribution"
											subtitle={`${$selectedSystem.toLowerCase() === 'washer' ? 'Down' : 'UV Down'} defects by X position - ${currentRangeLabel}`}
											data={orientationData}
											color={chartColors.primary}
											xAxisLabel="X Position (pixels)"
											yAxisLabel="Defect Count"
											{isDark}
											height={300}
										/>
									</div>
								{/if}

							{:else if $selectedSecondaryOption === 'coating'}
								<!-- Coating View (UVBC only) -->
								{#if $selectedSystem.toLowerCase() !== 'uvbc'}
									<div
										class="p-8 rounded-lg border text-center {isDark
											? 'bg-gray-800/50 border-gray-700/50 text-gray-400'
											: 'bg-white border-gray-200 text-gray-500'}"
									>
										<p class="text-sm">Coating metrics only available for UVBC system</p>
										<p class="text-xs mt-1">Select UVBC system to view intensity data</p>
									</div>
								{:else if coatingLoading}
									<div class="flex items-center justify-center h-32">
										<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
									</div>
								{:else if coatingError}
									<div
										class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}"
									>
										{coatingError}
									</div>
								{:else}
									<div class="space-y-4">
										<!-- Intensity Chart -->
										<div
											class="p-4 rounded-lg border {isDark
												? 'bg-gray-800/50 border-gray-700/50'
												: 'bg-white border-gray-200'}"
										>
											<h4 class="text-sm font-semibold mb-2 {isDark ? 'text-white' : 'text-gray-900'}">
												Ring Intensity (Daily Average)
											</h4>
											{#if intensityData.length > 0}
												<LineChart
													title=""
													subtitle=""
													data={intensityData.map(d => ({ time: d.date || d.time, value: d.avg_intensity || d.average_intensity || 0 }))}
													color={chartColors.primary}
													{isDark}
													height={200}
												/>
											{:else}
												<p class="text-sm text-center py-8 {isDark ? 'text-gray-500' : 'text-gray-400'}">
													No intensity data available
												</p>
											{/if}
										</div>

										<!-- Partial Rings Distribution -->
										<div
											class="p-4 rounded-lg border {isDark
												? 'bg-gray-800/50 border-gray-700/50'
												: 'bg-white border-gray-200'}"
										>
											<h4 class="text-sm font-semibold mb-2 {isDark ? 'text-white' : 'text-gray-900'}">
												Partial Ring Distribution
											</h4>
											{#if partialRingsData.length > 0}
												<HistogramChart
													title=""
													subtitle=""
													data={partialRingsData.map(d => ({ bin_start: Math.round(d.ring_percentage), bin_end: Math.round(d.ring_percentage) + 10, count: d.count }))}
													color={chartColors.secondary || '#f59e0b'}
													xAxisLabel="Ring Coverage %"
													yAxisLabel="Count"
													{isDark}
													height={200}
												/>
											{:else}
												<p class="text-sm text-center py-8 {isDark ? 'text-gray-500' : 'text-gray-400'}">
													No partial ring data available
												</p>
											{/if}
										</div>
									</div>
								{/if}

							{:else if $selectedSecondaryOption === 'system'}
								<!-- System Health View -->
								<div class="space-y-4">
									{#if systemHealthLoading}
										<div class="flex items-center justify-center h-32">
											<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
										</div>
									{:else if systemHealthError}
										<div class="p-4 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
											{systemHealthError}
										</div>
									{:else if systemHealthData.length === 0}
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
											{#each systemHealthData as device}
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

							<!-- Incidents Section -->
							<div class="space-y-3 mt-6">
								<h3 class="text-sm font-semibold {isDark ? 'text-white' : 'text-gray-900'}">
									Recent Incidents ({currentRangeLabel})
								</h3>
								<IncidentsList
									incidents={incidentsData}
									system={$selectedSystem.toLowerCase()}
									{isDark}
									loading={incidentsLoading}
									error={incidentsError}
								/>
							</div>
						{/if}

					</div>
				{/if}
			{/if}
		{/if}
	</div>
</div>
