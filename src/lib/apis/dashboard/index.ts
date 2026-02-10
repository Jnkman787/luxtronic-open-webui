/**
 * Dashboard API Client
 * Generic, tenant-configurable dashboard API client
 */

import { WEBUI_API_BASE_URL } from '$lib/constants';

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

export type TenantDashboardInfo = {
	id: string;
	display_name: string;
	tenant_group_name?: string | null;
	factory_name?: string | null;
	dashboard_type?: string | null;
};

export type MetricDefinition = {
	column: string;
	label: string;
};

export type InsightItem = {
	title: string;
	description: string;
};

export type DashboardSolution = {
	id: string;
	display_name: string;
	device_keys: string[];
};

export type DashboardLine = {
	id: string;
	display_name: string;
	solutions: Record<string, DashboardSolution>;
};

export type DashboardFactory = {
	id: string;
	display_name: string;
	timezone?: string | null;
	lines: Record<string, DashboardLine>;
};

export type DashboardView = {
	id: string;
	display_name: string;
	dashboard_type?: string | null;
	factory_id?: string | null;
	line_ids: string[];
	solution_ids: string[];
	time_ranges?: string[] | null;
};

export type TenantDashboardConfig = {
	id: string;
	display_name: string;
	tenant_group_name?: string | null;
	factory_id?: string | null;
	factory_name?: string | null;
	factories?: Record<string, DashboardFactory> | null;
	dashboard_views?: DashboardView[] | null;
	time_ranges?: string[] | null;
	dashboard_type?: string;
	available_lines: string[];
	available_systems: string[];
	line_systems?: Record<string, string[]>;
	metrics: Record<string, MetricDefinition>;
	default_period_days: number;
	shift_hours?: number | null;
	shift_bin_minutes?: number | null;
	shift_options?: { id: string; label: string }[] | null;
	shift_default?: string | null;
	shift_timeseries_scope?: string | null;
	defect_classes?: string[] | null;
	finalcheck_line_id?: string | null;
	insights?: InsightItem[] | null;
	insights_by_system?: Record<string, InsightItem[]> | null;
};

export type OverviewMetric = {
	device_id: string;
	line: string | null;
	system: string | null;
	total_units: number | null;  // null when washer can data unavailable
	defect_count: number;
	dpmo: number | null;  // null when total_units unknown
	dpmo_estimated: boolean;  // true when DPMO is based on estimated totals
	change_percent: number;
	historical_dpmo: number | null;  // historical average DPMO for comparison
};

export type OverviewResponse = {
	tenant_id: string;
	metrics: OverviewMetric[];
	period_days: number;
};

export type LineMetrics = {
	tenant_id: string;
	line_id: string;
	system: string;
	device_id: string | null;
	avg_fps: number;
	metrics: Record<string, number>;
};

export type Incident = {
	time: string;
	device_id: string;
	line_id: string;
	system: string;
	inc_hits: number;
	uuid: string | null;
	image_url: string | null;
	// Washer-specific fields
	down: number | null;
	inverted: number | null;
	down_conf: number | null;
	inverted_conf: number | null;
	can: number | null;
	can_conf: number | null;
	ring: number | null;
	ring_conf: number | null;
	empty_mat: number | null;
	empty_mat_conf: number | null;
	gate: number | null;
	gate_conf: number | null;
	empty: number | null;
	upside_down: number | null;
	broken_glass: number | null;
	// UVBC-specific fields
	uvdown: number | null;
	nocoating: number | null;
	uvpartial: number | null;
	edge: number | null;
	blob: number | null;
	uvdown_conf: number | null;
	nocoating_conf: number | null;
	uvpartial_conf: number | null;
	edge_conf: number | null;
	blob_conf: number | null;
	// Sidewall-specific fields
	defect_class: string | null;
	subtype: string | null;
	conf: number | null;
	reject: number | null;
	size_w: number | null;
	size_h: number | null;
	size_area: number | null;
};

export type IncidentsResponse = {
	tenant_id: string;
	line_id: string;
	incidents: Incident[];
	total: number;
};

export type TimeSeriesPoint = {
	time: string;
	value: number;
};

export type TimeSeriesResponse = {
	tenant_id: string;
	line_id: string;
	metric: string;
	data: TimeSeriesPoint[];
	period_days: number;
};

export type IntensityStats = {
	date: string;
	avg_intensity: number;
	min_intensity: number;
	max_intensity: number;
};

export type IntensityResponse = {
	tenant_id: string;
	line_id: string;
	data: IntensityStats[];
};

export type PartialRingData = {
	ring_percentage: number;
	count: number;
};

export type PartialRingResponse = {
	tenant_id: string;
	line_id: string;
	data: PartialRingData[];
};

export type OrientationBin = {
	bin_start: number;
	bin_end: number;
	count: number;
};

export type OrientationResponse = {
	tenant_id: string;
	line_id: string;
	system: string;
	defect_type: string;
	bin_size: number;
	data: OrientationBin[];
};

export type DeviceHealth = {
	device_id: string;
	line_id: string;
	system: string;
	status: 'ok' | 'warning' | 'error' | 'offline';
	last_seen: string | null;
	latest_fps: number | null;
	message: string | null;
};

export type SystemHealthResponse = {
	tenant_id: string;
	devices: DeviceHealth[];
	timestamp: string;
};

// =============================================================================
// SHIFT DASHBOARD TYPES
// =============================================================================

export type ShiftSnapshotItem = {
	label: string;
	device_id: string;
	total_units: number;
	change_percent: number | null;
};

export type ShiftSnapshotResponse = {
	tenant_id: string;
	shift_hours: number;
	shift_label: string;
	totals: ShiftSnapshotItem[];
};

export type ShiftThroughputResponse = {
	tenant_id: string;
	line_id: string;
	left_label: string;
	right_label: string;
	left_total: number;
	right_total: number;
	diff_units: number;
	diff_percent: number | null;
};

export type ShiftDownItem = {
	label: string;
	device_id: string;
	down_units: number;
};

export type ShiftDownResponse = {
	tenant_id: string;
	line_id: string;
	totals: ShiftDownItem[];
};

export type ShiftSeries = {
	label: string;
	data: TimeSeriesPoint[];
};

export type ShiftTimeSeriesResponse = {
	tenant_id: string;
	line_id: string;
	metric: string;
	series: ShiftSeries[];
	shift_hours: number;
	bin_minutes: number;
};

export type ShiftIncidentsResponse = {
	tenant_id: string;
	line_id: string;
	incidents: Incident[];
	total: number;
};

// =============================================================================
// CASE INSPECTION DASHBOARD TYPES
// =============================================================================

export type CaseInspectionShopSnapshot = {
	shop_id: string;
	device_id: string;
	total_cases: number;
	total_defects: number;
	dpmo: number | null;
};

export type CaseInspectionSnapshotResponse = {
	tenant_id: string;
	period_days: number;
	facility_cases: number;
	facility_defects: number;
	facility_dpmo: number | null;
	shops: CaseInspectionShopSnapshot[];
};

export type CaseInspectionThroughputResponse = {
	tenant_id: string;
	shop_id: string;
	device_id: string;
	total_cases: number;
	period_days: number;
	trend: TimeSeriesPoint[];
};

export type CaseInspectionDefectSeries = {
	label: string;
	data: TimeSeriesPoint[];
};

export type CaseInspectionDefectsResponse = {
	tenant_id: string;
	shop_id: string;
	period_days: number;
	totals: Record<string, number>;
	series: CaseInspectionDefectSeries[];
};

export type CaseInspectionIncidentsResponse = {
	tenant_id: string;
	shop_id: string;
	period_days: number;
	incidents: Incident[];
	total: number;
};

// =============================================================================
// LEHR INSPECTION DASHBOARD TYPES
// =============================================================================

export type LehrSnapshotResponse = {
	tenant_id: string;
	period_days: number;
	range_hours: number | null;
	total_units: number;
	total_change_percent: number | null;
	down_units: number;
	down_change_percent: number | null;
	empty_units: number;
	empty_change_percent: number | null;
};

export type LehrTotals = {
	ring: number;
	down: number;
	empty?: number | null;
};

export type LehrMetricSeries = {
	label: string;
	data: TimeSeriesPoint[];
};

export type LehrMetricsResponse = {
	tenant_id: string;
	period_days: number;
	range_hours: number | null;
	totals: LehrTotals;
	trend: LehrMetricSeries[];
	locations: LehrMetricSeries[];
};

export type LehrDumpGateResponse = {
	tenant_id: string;
	period_days: number;
	range_hours: number | null;
	total_ring: number;
	total_down: number;
	total_lost: number;
	open_seconds: number;
	open_trend: TimeSeriesPoint[];
};

export type LehrIncidentsResponse = {
	tenant_id: string;
	period_days: number;
	range_hours: number | null;
	incidents: Incident[];
	total: number;
};

// =============================================================================
// FINALCHECK DASHBOARD TYPES
// =============================================================================

export type FinalCheckSnapshot = {
	accumulation: number;
	divider: number;
	slipsheet: number;
};

export type FinalCheckSnapshotResponse = {
	tenant_id: string;
	line_id: string;
	counts: FinalCheckSnapshot;
};

export type FinalCheckDefectBar = {
	label: string;
	count: number;
};

export type FinalCheckDefectsResponse = {
	tenant_id: string;
	line_id: string;
	defects: FinalCheckDefectBar[];
};

export type FinalCheckIncident = {
	time: string;
	id: string;
	cell: string;
	class_name: string | null;
	confidence: number | null;
	anomaly_score: number | null;
	extra_one: number | null;
	extra_two: number | null;
	site: string | null;
	line: string | null;
	device: string | null;
	image_url: string | null;
	image_url_png: string | null;
};

export type FinalCheckIncidentsResponse = {
	tenant_id: string;
	line_id: string;
	incidents: FinalCheckIncident[];
	total: number;
};

// =============================================================================
// SIDEWALL DASHBOARD TYPES
// =============================================================================

export type SidewallDefectTotal = {
	defect_class: string;
	total: number;
};

export type SidewallSnapshotResponse = {
	tenant_id: string;
	period_days: number;
	total_inspections: number;
	total_defects: number;
	dpmo: number | null;
	defects: SidewallDefectTotal[];
};

export type SidewallInspectionsResponse = {
	tenant_id: string;
	period_days: number;
	total_inspections: number;
	total_jars: number | null;
	total_rejects: number;
	reject_rate: number | null;
	trend: TimeSeriesPoint[];
};

export type SidewallSeries = {
	label: string;
	data: TimeSeriesPoint[];
};

export type SidewallDefectResponse = {
	tenant_id: string;
	defect_class: string;
	period_days: number;
	total_defects: number;
	rate_by_inspections: number | null;
	percent_of_defects: number | null;
	series: SidewallSeries[];
};

export type SidewallIncidentsResponse = {
	tenant_id: string;
	defect_class: string;
	period_days: number;
	incidents: Incident[];
	total: number;
};

// =============================================================================
// SCALE WEIGHT DASHBOARD TYPES
// =============================================================================

export type ScaleSnapshotItem = {
	system_id: string;
	total_weight: number;
	change_percent: number | null;
};

export type ScaleSnapshotResponse = {
	tenant_id: string;
	period_days: number;
	range_hours: number | null;
	items: ScaleSnapshotItem[];
};

export type ScaleSeries = {
	label: string;
	data: TimeSeriesPoint[];
};

export type ScaleOverviewResponse = {
	tenant_id: string;
	system_id: string;
	period_days: number;
	range_hours: number | null;
	series: ScaleSeries[];
	fill_counts: Record<string, number>;
};

export type ScaleBayMetricsResponse = {
	tenant_id: string;
	system_id: string;
	bay: number;
	period_days: number;
	range_hours: number | null;
	total_net_weight: number;
	fill_count: number;
	tare_stddev: number;
	net_stddev: number;
};

export type ScaleBayTableRow = {
	time: string;
	box_id?: string | null;
	box_star?: string | null;
	net_weight?: number | null;
	tare_weight?: number | null;
	gross_weight?: number | null;
	job_total?: number | null;
	scale_number?: string | null;
	fill_stamp?: string | null;
	consecutive_number?: number | null;
	uuid?: string | null;
};

export type ScaleBayTableResponse = {
	tenant_id: string;
	system_id: string;
	bay: number;
	period_days: number;
	range_hours: number | null;
	rows: ScaleBayTableRow[];
	total: number;
};

export type ScaleImage = {
	time: string;
	uuid?: string | null;
	device_id?: string | null;
	image_url?: string | null;
};

export type ScaleBinImagesResponse = {
	tenant_id: string;
	system_id: string;
	bay: number;
	period_days: number;
	range_hours: number | null;
	images: ScaleImage[];
	total: number;
};

export type ScaleFailureCount = {
	label: string;
	device_id?: string | null;
	count: number;
};

export type ScaleFailureRow = {
	host?: string | null;
	time: string;
	device_id?: string | null;
	exception?: string | null;
	message?: string | null;
	failed?: number | null;
};

export type ScaleCameraHealthResponse = {
	tenant_id: string;
	system_id: string;
	period_days: number;
	range_hours: number | null;
	counts: ScaleFailureCount[];
	failures: ScaleFailureRow[];
	total: number;
};

// =============================================================================
// API FUNCTIONS
// =============================================================================

/**
 * Get list of available tenant dashboards
 */
export const getAvailableDashboards = async (token: string): Promise<TenantDashboardInfo[]> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch dashboards' }));
		throw new Error(error.detail || 'Failed to fetch dashboards');
	}

	const data = await res.json();
	return data.tenants;
};

/**
 * Get configuration for a specific tenant dashboard
 */
export const getTenantConfig = async (
	token: string,
	tenantId: string
): Promise<TenantDashboardConfig> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/config`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch tenant config' }));
		throw new Error(error.detail || 'Failed to fetch tenant config');
	}

	return res.json();
};

/**
 * Get overview metrics for a tenant
 */
export const getOverview = async (
	token: string,
	tenantId: string,
	days: number = 7,
	options: { shiftFilter?: string; rangeHours?: number } = {}
): Promise<OverviewResponse> => {
	const params = new URLSearchParams({ days: days.toString() });
	if (options.rangeHours) params.set('range_hours', String(options.rangeHours));
	if (options.shiftFilter) params.set('shift_filter', options.shiftFilter);

	const res = await fetch(
		`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/overview?${params}`,
		{
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		}
	);

	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch overview' }));
		throw new Error(error.detail || 'Failed to fetch overview');
	}

	return res.json();
};

/**
 * Get detailed metrics for a specific line
 */
export const getLineMetrics = async (
	token: string,
	tenantId: string,
	lineId: string,
	system: string = 'uvbc',
	days: number = 7,
	options: { shiftFilter?: string; rangeHours?: number } = {}
): Promise<LineMetrics> => {
	const params = new URLSearchParams({
		system,
		days: days.toString()
	});
	if (options.rangeHours) params.set('range_hours', String(options.rangeHours));
	if (options.shiftFilter) params.set('shift_filter', options.shiftFilter);

	const res = await fetch(
		`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/lines/${lineId}/metrics?${params}`,
		{
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		}
	);

	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch line metrics' }));
		throw new Error(error.detail || 'Failed to fetch line metrics');
	}

	return res.json();
};

/**
 * Get incidents for a line
 */
export const getIncidents = async (
	token: string,
	tenantId: string,
	lineId: string,
	options: {
		system?: string;
		limit?: number;
		largeOnly?: boolean;
		days?: number;
		shiftFilter?: string;
		rangeHours?: number;
	} = {}
): Promise<IncidentsResponse> => {
	const { system = 'washer', limit = 50, largeOnly = false, days = 7 } = options;

	const params = new URLSearchParams({
		system,
		limit: limit.toString(),
		large_only: largeOnly.toString(),
		days: days.toString()
	});
	if (options.rangeHours) params.set('range_hours', String(options.rangeHours));
	if (options.shiftFilter) params.set('shift_filter', options.shiftFilter);

	const res = await fetch(
		`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/lines/${lineId}/incidents?${params}`,
		{
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		}
	);

	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch incidents' }));
		throw new Error(error.detail || 'Failed to fetch incidents');
	}

	return res.json();
};

/**
 * Get time series data for charting
 */
export const getTimeSeries = async (
	token: string,
	tenantId: string,
	lineId: string,
	metric: string = 'down',
	system: string = 'uvbc',
	days: number = 14,
	options: { shiftFilter?: string; rangeHours?: number } = {}
): Promise<TimeSeriesResponse> => {
	const params = new URLSearchParams({
		metric,
		system,
		days: days.toString()
	});
	if (options.rangeHours) params.set('range_hours', String(options.rangeHours));
	if (options.shiftFilter) params.set('shift_filter', options.shiftFilter);

	const res = await fetch(
		`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/lines/${lineId}/timeseries?${params}`,
		{
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		}
	);

	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch time series' }));
		throw new Error(error.detail || 'Failed to fetch time series');
	}

	return res.json();
};

/**
 * Get UVBC intensity data
 */
export const getUVBCIntensity = async (
	token: string,
	tenantId: string,
	lineId: string,
	days: number = 7,
	options: { shiftFilter?: string; rangeHours?: number } = {}
): Promise<IntensityResponse> => {
	const params = new URLSearchParams({ days: days.toString() });
	if (options.rangeHours) params.set('range_hours', String(options.rangeHours));
	if (options.shiftFilter) params.set('shift_filter', options.shiftFilter);
	const res = await fetch(
		`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/uvbc/${lineId}/intensity?${params}`,
		{
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		}
	);

	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch UVBC intensity' }));
		throw new Error(error.detail || 'Failed to fetch UVBC intensity');
	}

	return res.json();
};

/**
 * Get partial ring data
 */
export const getPartialRings = async (
	token: string,
	tenantId: string,
	lineId: string,
	days: number = 7,
	options: { shiftFilter?: string; rangeHours?: number } = {}
): Promise<PartialRingResponse> => {
	const params = new URLSearchParams({ days: days.toString() });
	if (options.rangeHours) params.set('range_hours', String(options.rangeHours));
	if (options.shiftFilter) params.set('shift_filter', options.shiftFilter);
	const res = await fetch(
		`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/uvbc/${lineId}/partials?${params}`,
		{
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		}
	);

	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch partial rings' }));
		throw new Error(error.detail || 'Failed to fetch partial rings');
	}

	return res.json();
};

/**
 * Get defect orientation/location distribution
 */
export const getOrientation = async (
	token: string,
	tenantId: string,
	lineId: string,
	options: {
		system?: string;
		defectType?: string;
		days?: number;
		binSize?: number;
		shiftFilter?: string;
		rangeHours?: number;
	} = {}
): Promise<OrientationResponse> => {
	const { system = 'washer', defectType = 'down', days = 7, binSize = 100 } = options;

	const params = new URLSearchParams({
		system,
		defect_type: defectType,
		days: days.toString(),
		bin_size: binSize.toString()
	});
	if (options.rangeHours) params.set('range_hours', String(options.rangeHours));
	if (options.shiftFilter) params.set('shift_filter', options.shiftFilter);

	const res = await fetch(
		`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/lines/${lineId}/orientation?${params}`,
		{
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		}
	);

	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch orientation data' }));
		throw new Error(error.detail || 'Failed to fetch orientation data');
	}

	return res.json();
};

/**
 * Clear dashboard cache (admin only)
 */
export const clearDashboardCache = async (token: string): Promise<{ status: string; message: string }> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/cache/clear`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to clear cache' }));
		throw new Error(error.detail || 'Failed to clear cache');
	}

	return res.json();
};

/**
 * Get system health status for all devices
 */
export const getSystemHealth = async (
	token: string,
	tenantId: string,
	minutes: number = 30
): Promise<SystemHealthResponse> => {
	const res = await fetch(
		`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/health?minutes=${minutes}`,
		{
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		}
	);

	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch system health' }));
		throw new Error(error.detail || 'Failed to fetch system health');
	}

	return res.json();
};

// =============================================================================
// SHIFT DASHBOARD API
// =============================================================================

export const getShiftSnapshot = async (
	token: string,
	tenantId: string,
	options: {
		shiftHours?: number;
		excludeBlackout?: boolean;
		shiftFilter?: string;
		rangeHours?: number;
		days?: number;
	} = {}
): Promise<ShiftSnapshotResponse> => {
	const params = new URLSearchParams({
		shift_hours: String(options.shiftHours ?? 12),
		exclude_blackout: String(options.excludeBlackout ?? false)
	});
	if (options.shiftFilter) params.set('shift_filter', options.shiftFilter);
	if (options.rangeHours) params.set('range_hours', String(options.rangeHours));
	if (options.days) params.set('days', String(options.days));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/shift/snapshot?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch snapshot' }));
		throw new Error(error.detail || 'Failed to fetch snapshot');
	}
	return res.json();
};

export const getShiftThroughput = async (
	token: string,
	tenantId: string,
	lineId: string,
	options: {
		shiftHours?: number;
		excludeBlackout?: boolean;
		shiftFilter?: string;
		rangeHours?: number;
		days?: number;
	} = {}
): Promise<ShiftThroughputResponse> => {
	const params = new URLSearchParams({
		line_id: lineId,
		shift_hours: String(options.shiftHours ?? 12),
		exclude_blackout: String(options.excludeBlackout ?? false)
	});
	if (options.shiftFilter) params.set('shift_filter', options.shiftFilter);
	if (options.rangeHours) params.set('range_hours', String(options.rangeHours));
	if (options.days) params.set('days', String(options.days));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/shift/throughput?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch throughput' }));
		throw new Error(error.detail || 'Failed to fetch throughput');
	}
	return res.json();
};

export const getShiftDown = async (
	token: string,
	tenantId: string,
	lineId: string,
	options: {
		shiftHours?: number;
		excludeBlackout?: boolean;
		shiftFilter?: string;
		rangeHours?: number;
		days?: number;
	} = {}
): Promise<ShiftDownResponse> => {
	const params = new URLSearchParams({
		line_id: lineId,
		shift_hours: String(options.shiftHours ?? 12),
		exclude_blackout: String(options.excludeBlackout ?? false)
	});
	if (options.shiftFilter) params.set('shift_filter', options.shiftFilter);
	if (options.rangeHours) params.set('range_hours', String(options.rangeHours));
	if (options.days) params.set('days', String(options.days));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/shift/down?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch down totals' }));
		throw new Error(error.detail || 'Failed to fetch down totals');
	}
	return res.json();
};

export const getShiftTimeSeries = async (
	token: string,
	tenantId: string,
	lineId: string,
	metric: string,
	options: {
		shiftHours?: number;
		binMinutes?: number;
		excludeBlackout?: boolean;
		shiftFilter?: string;
		rangeHours?: number;
		days?: number;
	} = {}
): Promise<ShiftTimeSeriesResponse> => {
	const params = new URLSearchParams({
		line_id: lineId,
		metric,
		shift_hours: String(options.shiftHours ?? 12),
		bin_minutes: String(options.binMinutes ?? 10),
		exclude_blackout: String(options.excludeBlackout ?? false)
	});
	if (options.shiftFilter) params.set('shift_filter', options.shiftFilter);
	if (options.rangeHours) params.set('range_hours', String(options.rangeHours));
	if (options.days) params.set('days', String(options.days));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/shift/timeseries?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch timeseries' }));
		throw new Error(error.detail || 'Failed to fetch timeseries');
	}
	return res.json();
};

export const getShiftIncidents = async (
	token: string,
	tenantId: string,
	lineId: string,
	options: {
		rangeHours?: number;
		days?: number;
		limit?: number;
		excludeBlackout?: boolean;
		shiftFilter?: string;
	} = {}
): Promise<ShiftIncidentsResponse> => {
	const params = new URLSearchParams({ line_id: lineId });
	if (options.rangeHours) params.set('range_hours', String(options.rangeHours));
	if (options.days) params.set('days', String(options.days));
	if (options.limit) params.set('limit', String(options.limit));
	if (options.excludeBlackout !== undefined) {
		params.set('exclude_blackout', String(options.excludeBlackout));
	}
	if (options.shiftFilter) params.set('shift_filter', options.shiftFilter);
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/shift/incidents?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch incidents' }));
		throw new Error(error.detail || 'Failed to fetch incidents');
	}
	return res.json();
};

// =============================================================================
// CASE INSPECTION DASHBOARD API
// =============================================================================

export const getCaseInspectionSnapshot = async (
	token: string,
	tenantId: string,
	days: number = 7,
	rangeHours?: number
): Promise<CaseInspectionSnapshotResponse> => {
	const params = new URLSearchParams({ days: String(days) });
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(
		`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/case-inspection/snapshot?${params}`,
		{
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		}
	);
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch case inspection snapshot' }));
		throw new Error(error.detail || 'Failed to fetch case inspection snapshot');
	}
	return res.json();
};

export const getCaseInspectionThroughput = async (
	token: string,
	tenantId: string,
	shopId: string,
	days: number = 7,
	rangeHours?: number
): Promise<CaseInspectionThroughputResponse> => {
	const params = new URLSearchParams({
		shop_id: shopId,
		days: String(days)
	});
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(
		`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/case-inspection/throughput?${params}`,
		{
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		}
	);
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch case inspection throughput' }));
		throw new Error(error.detail || 'Failed to fetch case inspection throughput');
	}
	return res.json();
};

export const getCaseInspectionDefects = async (
	token: string,
	tenantId: string,
	shopId: string,
	days: number = 7,
	rangeHours?: number
): Promise<CaseInspectionDefectsResponse> => {
	const params = new URLSearchParams({
		shop_id: shopId,
		days: String(days)
	});
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(
		`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/case-inspection/defects?${params}`,
		{
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		}
	);
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch case inspection defects' }));
		throw new Error(error.detail || 'Failed to fetch case inspection defects');
	}
	return res.json();
};

export const getCaseInspectionIncidents = async (
	token: string,
	tenantId: string,
	shopId: string,
	days: number = 7,
	limit: number = 10,
	rangeHours?: number
): Promise<CaseInspectionIncidentsResponse> => {
	const params = new URLSearchParams({
		shop_id: shopId,
		days: String(days),
		limit: String(limit)
	});
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(
		`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/case-inspection/incidents?${params}`,
		{
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		}
	);
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch case inspection incidents' }));
		throw new Error(error.detail || 'Failed to fetch case inspection incidents');
	}
	return res.json();
};

// =============================================================================
// LEHR INSPECTION DASHBOARD API
// =============================================================================

export const getLehrSnapshot = async (
	token: string,
	tenantId: string,
	days: number = 7,
	rangeHours?: number
): Promise<LehrSnapshotResponse> => {
	const params = new URLSearchParams({ days: String(days) });
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/lehr/snapshot?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch Lehr snapshot' }));
		throw new Error(error.detail || 'Failed to fetch Lehr snapshot');
	}
	return res.json();
};

export const getLehrOverhead = async (
	token: string,
	tenantId: string,
	days: number = 7,
	rangeHours?: number,
	limit: number = 1000
): Promise<LehrMetricsResponse> => {
	const params = new URLSearchParams({
		days: String(days),
		limit: String(limit)
	});
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/lehr/overhead?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch Lehr overhead metrics' }));
		throw new Error(error.detail || 'Failed to fetch Lehr overhead metrics');
	}
	return res.json();
};

export const getLehrExit = async (
	token: string,
	tenantId: string,
	days: number = 7,
	rangeHours?: number,
	limit: number = 1000
): Promise<LehrMetricsResponse> => {
	const params = new URLSearchParams({
		days: String(days),
		limit: String(limit)
	});
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/lehr/exit?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch Lehr exit metrics' }));
		throw new Error(error.detail || 'Failed to fetch Lehr exit metrics');
	}
	return res.json();
};

export const getLehrDumpGate = async (
	token: string,
	tenantId: string,
	days: number = 7,
	rangeHours?: number
): Promise<LehrDumpGateResponse> => {
	const params = new URLSearchParams({ days: String(days) });
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/lehr/dump-gate?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch Lehr dump gate metrics' }));
		throw new Error(error.detail || 'Failed to fetch Lehr dump gate metrics');
	}
	return res.json();
};

export const getLehrIncidents = async (
	token: string,
	tenantId: string,
	days: number = 7,
	rangeHours?: number,
	limit: number = 30
): Promise<LehrIncidentsResponse> => {
	const params = new URLSearchParams({
		days: String(days),
		limit: String(limit)
	});
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/lehr/incidents?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch Lehr incidents' }));
		throw new Error(error.detail || 'Failed to fetch Lehr incidents');
	}
	return res.json();
};

// =============================================================================
// FINALCHECK DASHBOARD API
// =============================================================================

export const getFinalCheckSnapshot = async (
	token: string,
	tenantId: string,
	lineId: string,
	days: number = 7,
	rangeHours?: number
): Promise<FinalCheckSnapshotResponse> => {
	const params = new URLSearchParams({ line_id: lineId, days: String(days) });
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/finalcheck/snapshot?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch FinalCheck snapshot' }));
		throw new Error(error.detail || 'Failed to fetch FinalCheck snapshot');
	}
	return res.json();
};

export const getFinalCheckDefects = async (
	token: string,
	tenantId: string,
	lineId: string,
	days: number = 7,
	rangeHours?: number,
	limit: number = 9
): Promise<FinalCheckDefectsResponse> => {
	const params = new URLSearchParams({
		line_id: lineId,
		days: String(days),
		limit: String(limit)
	});
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/finalcheck/defects?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch FinalCheck defects' }));
		throw new Error(error.detail || 'Failed to fetch FinalCheck defects');
	}
	return res.json();
};

export const getFinalCheckIncidents = async (
	token: string,
	tenantId: string,
	lineId: string,
	days: number = 7,
	rangeHours?: number,
	limit: number = 30
): Promise<FinalCheckIncidentsResponse> => {
	const params = new URLSearchParams({
		line_id: lineId,
		days: String(days),
		limit: String(limit)
	});
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/finalcheck/incidents?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch FinalCheck incidents' }));
		throw new Error(error.detail || 'Failed to fetch FinalCheck incidents');
	}
	return res.json();
};

// =============================================================================
// SIDEWALL DASHBOARD API
// =============================================================================

export const getSidewallSnapshot = async (
	token: string,
	tenantId: string,
	days: number = 7,
	rangeHours?: number
): Promise<SidewallSnapshotResponse> => {
	const params = new URLSearchParams({ days: String(days) });
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/sidewall/snapshot?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch sidewall snapshot' }));
		throw new Error(error.detail || 'Failed to fetch sidewall snapshot');
	}
	return res.json();
};

export const getSidewallInspections = async (
	token: string,
	tenantId: string,
	days: number = 7,
	rangeHours?: number
): Promise<SidewallInspectionsResponse> => {
	const params = new URLSearchParams({ days: String(days) });
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/sidewall/inspections?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch sidewall inspections' }));
		throw new Error(error.detail || 'Failed to fetch sidewall inspections');
	}
	return res.json();
};

export const getSidewallDefect = async (
	token: string,
	tenantId: string,
	defectClass: string,
	days: number = 7,
	rangeHours?: number
): Promise<SidewallDefectResponse> => {
	const params = new URLSearchParams({
		defect_class: defectClass,
		days: String(days)
	});
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/sidewall/defect?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch sidewall defect data' }));
		throw new Error(error.detail || 'Failed to fetch sidewall defect data');
	}
	return res.json();
};

export const getSidewallIncidents = async (
	token: string,
	tenantId: string,
	defectClass: string,
	days: number = 7,
	limit: number = 10,
	rangeHours?: number
): Promise<SidewallIncidentsResponse> => {
	const params = new URLSearchParams({
		defect_class: defectClass,
		days: String(days),
		limit: String(limit)
	});
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/sidewall/incidents?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch sidewall incidents' }));
		throw new Error(error.detail || 'Failed to fetch sidewall incidents');
	}
	return res.json();
};

export const getSidewallHealth = async (
	token: string,
	tenantId: string,
	minutes: number = 30,
	cameraDays: number = 7
): Promise<SystemHealthResponse> => {
	const params = new URLSearchParams({
		minutes: String(minutes),
		camera_days: String(cameraDays)
	});
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/sidewall/health?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch sidewall health' }));
		throw new Error(error.detail || 'Failed to fetch sidewall health');
	}
	return res.json();
};

// =============================================================================
// SCALE WEIGHT DASHBOARD API
// =============================================================================

export const getScaleSnapshot = async (
	token: string,
	tenantId: string,
	days: number = 7,
	rangeHours?: number
): Promise<ScaleSnapshotResponse> => {
	const params = new URLSearchParams({ days: String(days) });
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/scale/snapshot?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch scale snapshot' }));
		throw new Error(error.detail || 'Failed to fetch scale snapshot');
	}
	return res.json();
};

export const getScaleOverview = async (
	token: string,
	tenantId: string,
	systemId: string,
	days: number = 7,
	rangeHours?: number
): Promise<ScaleOverviewResponse> => {
	const params = new URLSearchParams({
		system_id: systemId,
		days: String(days)
	});
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/scale/overview?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch scale overview' }));
		throw new Error(error.detail || 'Failed to fetch scale overview');
	}
	return res.json();
};

export const getScaleBayMetrics = async (
	token: string,
	tenantId: string,
	systemId: string,
	bay: number,
	days: number = 7,
	rangeHours?: number
): Promise<ScaleBayMetricsResponse> => {
	const params = new URLSearchParams({
		system_id: systemId,
		bay: String(bay),
		days: String(days)
	});
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/scale/bay-metrics?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch bay metrics' }));
		throw new Error(error.detail || 'Failed to fetch bay metrics');
	}
	return res.json();
};

export const getScaleBayTable = async (
	token: string,
	tenantId: string,
	systemId: string,
	bay: number,
	days: number = 7,
	rangeHours?: number,
	limit: number = 50
): Promise<ScaleBayTableResponse> => {
	const params = new URLSearchParams({
		system_id: systemId,
		bay: String(bay),
		days: String(days),
		limit: String(limit)
	});
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/scale/bay-table?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch bay table' }));
		throw new Error(error.detail || 'Failed to fetch bay table');
	}
	return res.json();
};

export const getScaleBinImages = async (
	token: string,
	tenantId: string,
	systemId: string,
	bay: number,
	days: number = 7,
	rangeHours?: number,
	limit: number = 15
): Promise<ScaleBinImagesResponse> => {
	const params = new URLSearchParams({
		system_id: systemId,
		bay: String(bay),
		days: String(days),
		limit: String(limit)
	});
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/scale/bin-images?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch bin images' }));
		throw new Error(error.detail || 'Failed to fetch bin images');
	}
	return res.json();
};

export const getScaleCameraHealth = async (
	token: string,
	tenantId: string,
	systemId: string,
	days: number = 7,
	rangeHours?: number,
	limit: number = 50
): Promise<ScaleCameraHealthResponse> => {
	const params = new URLSearchParams({
		system_id: systemId,
		days: String(days),
		limit: String(limit)
	});
	if (rangeHours) params.set('range_hours', String(rangeHours));
	const res = await fetch(`${WEBUI_API_BASE_URL}/dashboard/tenants/${tenantId}/scale/camera-health?${params}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});
	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'Failed to fetch camera health' }));
		throw new Error(error.detail || 'Failed to fetch camera health');
	}
	return res.json();
};
