"""
Pydantic models for Tenant Dashboard API responses
Generic models - no sensitive tenant configurations
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# =============================================================================
# TENANT CONFIGURATION MODELS
# =============================================================================

class TenantDashboardInfo(BaseModel):
    """Basic tenant dashboard info"""
    id: str
    display_name: str
    tenant_group_name: Optional[str] = None
    factory_name: Optional[str] = None
    dashboard_type: Optional[str] = None


class ShiftOption(BaseModel):
    """Shift selection option for dashboards"""
    id: str
    label: str


class InsightItem(BaseModel):
    """Dashboard insight card"""
    title: str
    description: str


class DashboardSolution(BaseModel):
    """Solution definition for a line"""
    id: str
    display_name: str
    device_keys: List[str] = []


class DashboardLine(BaseModel):
    """Line definition for a factory"""
    id: str
    display_name: str
    solutions: Dict[str, DashboardSolution] = {}


class DashboardFactory(BaseModel):
    """Factory/location definition"""
    id: str
    display_name: str
    timezone: Optional[str] = None
    lines: Dict[str, DashboardLine] = {}


class DashboardView(BaseModel):
    """Dashboard view metadata"""
    id: str
    display_name: str
    dashboard_type: Optional[str] = "quality"
    factory_id: Optional[str] = None
    line_ids: List[str] = []
    solution_ids: List[str] = []
    time_ranges: Optional[List[str]] = None


class TenantDashboardConfig(BaseModel):
    """Tenant dashboard configuration (populated by rag-platform)"""
    id: str
    display_name: str
    tenant_group_name: Optional[str] = None
    factory_id: Optional[str] = None
    factory_name: Optional[str] = None
    factories: Optional[Dict[str, DashboardFactory]] = None
    dashboard_views: Optional[List[DashboardView]] = None
    time_ranges: Optional[List[str]] = None
    dashboard_type: Optional[str] = "quality"
    available_lines: List[str]
    available_systems: List[str]
    line_systems: Optional[Dict[str, List[str]]] = None
    metrics: Dict[str, Dict[str, str]]
    default_period_days: int = 7
    shift_hours: Optional[int] = None
    shift_bin_minutes: Optional[int] = None
    shift_options: Optional[List[ShiftOption]] = None
    shift_default: Optional[str] = None
    shift_timeseries_scope: Optional[str] = None
    defect_classes: Optional[List[str]] = None
    finalcheck_line_id: Optional[str] = None
    insights: Optional[List[InsightItem]] = None
    insights_by_system: Optional[Dict[str, List[InsightItem]]] = None


class AvailableTenantDashboards(BaseModel):
    """List of available tenant dashboards"""
    tenants: List[TenantDashboardInfo]


# =============================================================================
# METRICS MODELS
# =============================================================================

class OverviewMetric(BaseModel):
    """Single line/device overview metric"""
    device_id: Optional[str] = None
    line: Optional[str] = None
    system: Optional[str] = None
    total_units: Optional[int] = None  # None when washer can data unavailable
    defect_count: int
    dpmo: Optional[float] = None  # None when total_units unknown
    dpmo_estimated: bool = False  # True when DPMO is based on estimated totals
    change_percent: float = 0.0
    historical_dpmo: Optional[float] = None  # Historical average DPMO for comparison


class OverviewResponse(BaseModel):
    """Overview metrics for all lines"""
    tenant_id: str
    metrics: List[OverviewMetric]
    period_days: int = 7


class LineMetrics(BaseModel):
    """Detailed metrics for a specific line"""
    tenant_id: str
    line_id: str
    system: str
    device_id: Optional[str] = None
    avg_fps: float = 0.0
    metrics: Dict[str, Any] = {}


# =============================================================================
# INCIDENT MODELS
# =============================================================================

class Incident(BaseModel):
    """Single incident record - supports both washer and UVBC systems"""
    time: str
    device_id: Optional[str] = None
    line_id: str
    system: str
    inc_hits: int
    uuid: Optional[str] = None
    image_url: Optional[str] = None
    # Washer-specific fields
    down: Optional[int] = None
    inverted: Optional[int] = None
    down_conf: Optional[float] = None
    inverted_conf: Optional[float] = None
    can: Optional[int] = None
    can_conf: Optional[float] = None
    ring: Optional[int] = None
    ring_conf: Optional[float] = None
    empty_mat: Optional[int] = None
    empty_mat_conf: Optional[float] = None
    gate: Optional[int] = None
    gate_conf: Optional[float] = None
    empty: Optional[int] = None
    upside_down: Optional[int] = None
    broken_glass: Optional[int] = None
    # UVBC-specific fields
    uvdown: Optional[int] = None
    nocoating: Optional[int] = None
    uvpartial: Optional[int] = None
    edge: Optional[int] = None
    blob: Optional[int] = None
    uvdown_conf: Optional[float] = None
    nocoating_conf: Optional[float] = None
    uvpartial_conf: Optional[float] = None
    edge_conf: Optional[float] = None
    blob_conf: Optional[float] = None
    # Sidewall-specific fields
    defect_class: Optional[str] = None
    subtype: Optional[str] = None
    conf: Optional[float] = None
    reject: Optional[int] = None
    size_w: Optional[float] = None
    size_h: Optional[float] = None
    size_area: Optional[float] = None


class IncidentsResponse(BaseModel):
    """List of incidents"""
    tenant_id: str
    line_id: str
    incidents: List[Incident]
    total: int


# =============================================================================
# TIME SERIES MODELS
# =============================================================================

class TimeSeriesPoint(BaseModel):
    """Single time series data point"""
    time: str
    value: float


class TimeSeriesResponse(BaseModel):
    """Time series data for charting"""
    tenant_id: str
    line_id: str
    metric: str
    data: List[TimeSeriesPoint]
    period_days: int


# =============================================================================
# UVBC SPECIFIC MODELS
# =============================================================================

class IntensityStats(BaseModel):
    """UVBC ring intensity statistics"""
    date: str
    avg_intensity: float
    min_intensity: float
    max_intensity: float


class IntensityResponse(BaseModel):
    """UVBC intensity data"""
    tenant_id: str
    line_id: str
    data: List[IntensityStats]


class PartialRingData(BaseModel):
    """Partial ring percentage distribution"""
    ring_percentage: float
    count: int


class PartialRingResponse(BaseModel):
    """Partial ring data response"""
    tenant_id: str
    line_id: str
    data: List[PartialRingData]


# =============================================================================
# UTILITY MODELS
# =============================================================================

class ImageUrlResponse(BaseModel):
    """Incident image URL response"""
    tenant_id: str
    uuid: str
    image_url: str


class CacheClearResponse(BaseModel):
    """Cache clear response"""
    status: str
    message: str


# =============================================================================
# ORIENTATION MODELS
# =============================================================================

class OrientationBin(BaseModel):
    """Single orientation histogram bin"""
    bin_start: int
    bin_end: int
    count: int


# =============================================================================
# FINALCHECK MODELS
# =============================================================================

class FinalCheckSnapshot(BaseModel):
    """FinalCheck snapshot counts by cell"""
    accumulation: int
    divider: int
    slipsheet: int


class FinalCheckSnapshotResponse(BaseModel):
    """Snapshot response for FinalCheck"""
    tenant_id: str
    line_id: str
    counts: FinalCheckSnapshot


class FinalCheckDefectBar(BaseModel):
    """Single defect bar value"""
    label: str
    count: int


class FinalCheckDefectsResponse(BaseModel):
    """Defect chart data for FinalCheck"""
    tenant_id: str
    line_id: str
    defects: List[FinalCheckDefectBar]


class FinalCheckIncident(BaseModel):
    """FinalCheck incident image record"""
    time: str
    id: str
    cell: str
    class_name: Optional[str] = None
    confidence: Optional[float] = None
    anomaly_score: Optional[float] = None
    extra_one: Optional[float] = None
    extra_two: Optional[float] = None
    site: Optional[str] = None
    line: Optional[str] = None
    device: Optional[str] = None
    image_url: Optional[str] = None
    image_url_png: Optional[str] = None


class FinalCheckIncidentsResponse(BaseModel):
    """FinalCheck incidents response"""
    tenant_id: str
    line_id: str
    incidents: List[FinalCheckIncident]
    total: int


class OrientationResponse(BaseModel):
    """Defect location distribution (x-position histogram)"""
    tenant_id: str
    line_id: str
    system: str
    defect_type: str
    bin_size: int
    data: List[OrientationBin]


# =============================================================================
# SYSTEM HEALTH MODELS
# =============================================================================

class DeviceHealth(BaseModel):
    """Health status for a single device/camera"""
    device_id: str
    line_id: str
    system: str
    status: str  # "ok", "warning", "error", "offline"
    last_seen: Optional[str] = None
    latest_fps: Optional[float] = None
    message: Optional[str] = None


class SystemHealthResponse(BaseModel):
    """System health status for all devices"""
    tenant_id: str
    devices: List[DeviceHealth]
    timestamp: str


# =============================================================================
# SHIFT DASHBOARD MODELS
# =============================================================================

class ShiftSnapshotItem(BaseModel):
    """Shift snapshot total for a single inspection point"""
    label: str
    device_id: str
    total_units: int
    change_percent: Optional[float] = None


class ShiftSnapshotResponse(BaseModel):
    """Shift snapshot totals"""
    tenant_id: str
    shift_hours: int
    shift_label: str
    totals: List[ShiftSnapshotItem]


class ShiftThroughputResponse(BaseModel):
    """Throughput difference between paired inspection points"""
    tenant_id: str
    line_id: str
    left_label: str
    right_label: str
    left_total: int
    right_total: int
    diff_units: int
    diff_percent: Optional[float] = None


class ShiftDownItem(BaseModel):
    """Down totals for a single inspection point"""
    label: str
    device_id: str
    down_units: int


class ShiftDownResponse(BaseModel):
    """Down totals for shift dashboard line"""
    tenant_id: str
    line_id: str
    totals: List[ShiftDownItem]


class ShiftSeries(BaseModel):
    """Timeseries for a single inspection point"""
    label: str
    data: List[TimeSeriesPoint]


class ShiftTimeSeriesResponse(BaseModel):
    """Timeseries response for shift dashboard"""
    tenant_id: str
    line_id: str
    metric: str
    series: List[ShiftSeries]
    shift_hours: int
    bin_minutes: int


class ShiftIncidentsResponse(BaseModel):
    """Incidents response for shift dashboard"""
    tenant_id: str
    line_id: str
    incidents: List[Incident]
    total: int


# =============================================================================
# CASE INSPECTION DASHBOARD MODELS
# =============================================================================

class CaseInspectionShopSnapshot(BaseModel):
    """Snapshot totals for a single case inspection shop"""
    shop_id: str
    device_id: str
    total_cases: int
    total_defects: int
    dpmo: Optional[float] = None


class CaseInspectionSnapshotResponse(BaseModel):
    """Facility snapshot for case inspection"""
    tenant_id: str
    period_days: int
    facility_cases: int
    facility_defects: int
    facility_dpmo: Optional[float] = None
    shops: List[CaseInspectionShopSnapshot]


class CaseInspectionThroughputResponse(BaseModel):
    """Throughput totals + trend for a case inspection shop"""
    tenant_id: str
    shop_id: str
    device_id: str
    total_cases: int
    period_days: int
    trend: List[TimeSeriesPoint]


class CaseInspectionDefectSeries(BaseModel):
    """Defect trend series for a case inspection shop"""
    label: str
    data: List[TimeSeriesPoint]


class CaseInspectionDefectsResponse(BaseModel):
    """Defect totals + trend for a case inspection shop"""
    tenant_id: str
    shop_id: str
    period_days: int
    totals: Dict[str, int]
    series: List[CaseInspectionDefectSeries]


class CaseInspectionIncidentsResponse(BaseModel):
    """Incidents for a case inspection shop"""
    tenant_id: str
    shop_id: str
    period_days: int
    incidents: List[Incident]
    total: int


# =============================================================================
# LEHR INSPECTION DASHBOARD MODELS
# =============================================================================

class LehrSnapshotResponse(BaseModel):
    """Snapshot totals for Lehr inspection"""
    tenant_id: str
    period_days: int
    range_hours: Optional[int] = None
    total_units: int
    total_change_percent: Optional[float] = None
    down_units: int
    down_change_percent: Optional[float] = None
    empty_units: int
    empty_change_percent: Optional[float] = None


class LehrTotals(BaseModel):
    """Totals for Lehr inspection metrics"""
    ring: int
    down: int
    empty: Optional[int] = None


class LehrMetricSeries(BaseModel):
    """Timeseries for Lehr inspection metrics"""
    label: str
    data: List[TimeSeriesPoint]


class LehrMetricsResponse(BaseModel):
    """Metrics response for Lehr inspection views"""
    tenant_id: str
    period_days: int
    range_hours: Optional[int] = None
    totals: LehrTotals
    trend: List[LehrMetricSeries]
    locations: List[LehrMetricSeries]


class LehrDumpGateResponse(BaseModel):
    """Dump gate metrics for Lehr inspection"""
    tenant_id: str
    period_days: int
    range_hours: Optional[int] = None
    total_ring: int
    total_down: int
    total_lost: int
    open_seconds: int
    open_trend: List[TimeSeriesPoint]


class LehrIncidentsResponse(BaseModel):
    """Incidents for Lehr inspection"""
    tenant_id: str
    period_days: int
    range_hours: Optional[int] = None
    incidents: List[Incident]
    total: int


# =============================================================================
# SIDEWALL DASHBOARD MODELS
# =============================================================================

class SidewallDefectTotal(BaseModel):
    """Defect totals for sidewall snapshot"""
    defect_class: str
    total: int


class SidewallSnapshotResponse(BaseModel):
    """Sidewall snapshot summary"""
    tenant_id: str
    period_days: int
    total_inspections: int
    total_defects: int
    dpmo: Optional[float] = None
    defects: List[SidewallDefectTotal]


class SidewallInspectionsResponse(BaseModel):
    """Sidewall inspections overview"""
    tenant_id: str
    period_days: int
    total_inspections: int
    total_jars: Optional[float] = None
    total_rejects: int
    reject_rate: Optional[float] = None
    trend: List[TimeSeriesPoint]


class SidewallSeries(BaseModel):
    """Sidewall defect trend series"""
    label: str
    data: List[TimeSeriesPoint]


class SidewallDefectResponse(BaseModel):
    """Sidewall defect detail response"""
    tenant_id: str
    defect_class: str
    period_days: int
    total_defects: int
    rate_by_inspections: Optional[float] = None
    percent_of_defects: Optional[float] = None
    series: List[SidewallSeries]


class SidewallIncidentsResponse(BaseModel):
    """Sidewall defect incidents response"""
    tenant_id: str
    defect_class: str
    period_days: int
    incidents: List[Incident]
    total: int


# =============================================================================
# SCALE WEIGHT DASHBOARD MODELS
# =============================================================================

class ScaleSnapshotItem(BaseModel):
    """Snapshot total for a single scale system"""
    system_id: str
    total_weight: float
    change_percent: Optional[float] = None


class ScaleSnapshotResponse(BaseModel):
    """Snapshot response for scale dashboard"""
    tenant_id: str
    period_days: int
    range_hours: Optional[int] = None
    items: List[ScaleSnapshotItem]


class ScaleSeries(BaseModel):
    """Time series for a scale bay"""
    label: str
    data: List[TimeSeriesPoint]


class ScaleOverviewResponse(BaseModel):
    """Overview response for scale dashboard"""
    tenant_id: str
    system_id: str
    period_days: int
    range_hours: Optional[int] = None
    series: List[ScaleSeries]
    fill_counts: Dict[str, int]


class ScaleBayMetricsResponse(BaseModel):
    """Bay metrics response for scale dashboard"""
    tenant_id: str
    system_id: str
    bay: int
    period_days: int
    range_hours: Optional[int] = None
    total_net_weight: float
    fill_count: int
    tare_stddev: float
    net_stddev: float


class ScaleBayTableRow(BaseModel):
    """Bay table row for scale dashboard"""
    time: str
    box_id: Optional[str] = None
    box_star: Optional[str] = None
    net_weight: Optional[float] = None
    tare_weight: Optional[float] = None
    gross_weight: Optional[float] = None
    job_total: Optional[float] = None
    scale_number: Optional[str] = None
    fill_stamp: Optional[str] = None
    consecutive_number: Optional[int] = None
    uuid: Optional[str] = None


class ScaleBayTableResponse(BaseModel):
    """Bay table response for scale dashboard"""
    tenant_id: str
    system_id: str
    bay: int
    period_days: int
    range_hours: Optional[int] = None
    rows: List[ScaleBayTableRow]
    total: int


class ScaleImage(BaseModel):
    """Bin image response item"""
    time: str
    uuid: Optional[str] = None
    device_id: Optional[str] = None
    image_url: Optional[str] = None


class ScaleBinImagesResponse(BaseModel):
    """Bin images response for scale dashboard"""
    tenant_id: str
    system_id: str
    bay: int
    period_days: int
    range_hours: Optional[int] = None
    images: List[ScaleImage]
    total: int


class ScaleFailureCount(BaseModel):
    """Camera failure count item"""
    label: str
    device_id: Optional[str] = None
    count: int


class ScaleFailureRow(BaseModel):
    """Camera failure detail row"""
    host: Optional[str] = None
    time: str
    device_id: Optional[str] = None
    exception: Optional[str] = None
    message: Optional[str] = None
    failed: Optional[int] = None


class ScaleCameraHealthResponse(BaseModel):
    """Camera health response for scale dashboard"""
    tenant_id: str
    system_id: str
    period_days: int
    range_hours: Optional[int] = None
    counts: List[ScaleFailureCount]
    failures: List[ScaleFailureRow]
    total: int
