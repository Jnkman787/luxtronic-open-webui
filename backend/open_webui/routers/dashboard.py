"""
Tenant Dashboard Router
Proxies dashboard requests to rag-platform backend.
All sensitive data and Timestream queries are handled by rag-platform.
"""

import logging
import re
from typing import Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Query

from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.models.tenants import Tenants
from open_webui.models.dashboard import (
    TenantDashboardInfo,
    TenantDashboardConfig,
    AvailableTenantDashboards,
    OverviewResponse,
    OverviewMetric,
    LineMetrics,
    IncidentsResponse,
    Incident,
    TimeSeriesResponse,
    TimeSeriesPoint,
    IntensityResponse,
    IntensityStats,
    PartialRingResponse,
    PartialRingData,
    ImageUrlResponse,
    CacheClearResponse,
    OrientationResponse,
    OrientationBin,
    SystemHealthResponse,
    DeviceHealth,
    ShiftSnapshotResponse,
    ShiftThroughputResponse,
    ShiftDownResponse,
    ShiftTimeSeriesResponse,
    ShiftIncidentsResponse,
    CaseInspectionSnapshotResponse,
    CaseInspectionThroughputResponse,
    CaseInspectionDefectsResponse,
    CaseInspectionIncidentsResponse,
    LehrSnapshotResponse,
    LehrMetricsResponse,
    LehrDumpGateResponse,
    LehrIncidentsResponse,
    FinalCheckSnapshotResponse,
    FinalCheckDefectsResponse,
    FinalCheckIncidentsResponse,
    SidewallSnapshotResponse,
    SidewallInspectionsResponse,
    SidewallDefectResponse,
    SidewallIncidentsResponse,
    ScaleSnapshotResponse,
    ScaleOverviewResponse,
    ScaleBayMetricsResponse,
    ScaleBayTableResponse,
    ScaleBinImagesResponse,
    ScaleCameraHealthResponse,
)
from open_webui.services import timestream

logger = logging.getLogger(__name__)

router = APIRouter()

def _normalize_dashboard_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").strip().lower())

ADMIN_ONLY_DASHBOARDS: Set[str] = set()
ADMIN_ONLY_DASHBOARDS_NORMALIZED = {
    re.sub(r"[^a-z0-9]+", "", value.strip().lower())
    for value in ADMIN_ONLY_DASHBOARDS
}


def _candidate_dashboard_ids_from_tenant(tenant) -> Set[str]:
    """
    Derive a set of dashboard tenant IDs that a non-admin user can access.

    We intentionally avoid introducing new schema fields by matching the rag-platform
    dashboard ID against identifiers already present on the tenant row.
    """
    candidates: Set[str] = set()

    def add(value: Optional[str]) -> None:
        if not value:
            return
        raw = value.strip().lower()
        if raw:
            candidates.add(raw)
        normalized = _normalize_dashboard_id(raw)
        if normalized:
            candidates.add(normalized)

    add(getattr(tenant, "s3_bucket", None))
    add(getattr(tenant, "table_name", None))
    add(getattr(tenant, "system_config_client_name", None))
    add(getattr(tenant, "name", None))
    add(getattr(tenant, "tenant_group_name", None))

    token_source = " ".join([
        getattr(tenant, "s3_bucket", "") or "",
        getattr(tenant, "table_name", "") or "",
        getattr(tenant, "system_config_client_name", "") or "",
        getattr(tenant, "name", "") or "",
        getattr(tenant, "tenant_group_name", "") or "",
    ]).strip().lower()
    if token_source:
        tokens = [t for t in re.split(r"[^a-z0-9]+", token_source) if t]
        if tokens:
            first = tokens[0]
            last = tokens[-1]
            candidates.update({first, last, f"{first}_{last}", f"{first}{last}"})

    return {c for c in candidates if c}

def _is_admin_only_dashboard(dashboard_id: str) -> bool:
    normalized = _normalize_dashboard_id(dashboard_id or "")
    return normalized in ADMIN_ONLY_DASHBOARDS_NORMALIZED


def _get_allowed_dashboard_ids(user) -> Optional[Set[str]]:
    """
    Returns:
      - None for admin users (meaning "all dashboards allowed")
      - A set of allowed dashboard tenant IDs for non-admin users
    """
    if getattr(user, "role", None) == "admin":
        return None

    user_tenant_id = getattr(user, "tenant_id", None)
    if not user_tenant_id:
        raise HTTPException(status_code=403, detail="User is not associated with a tenant")

    tenant = Tenants.get_tenant_by_id(user_tenant_id)
    if not tenant:
        raise HTTPException(status_code=403, detail="Tenant not found for user")

    allowed = _candidate_dashboard_ids_from_tenant(tenant)
    if not allowed:
        raise HTTPException(status_code=403, detail="Tenant is not configured for dashboards")
    return allowed


def _is_dashboard_allowed(allowed: Optional[Set[str]], dashboard_tenant_id: str) -> bool:
    if allowed is None:
        return True
    dashboard_id = (dashboard_tenant_id or "").lower()
    normalized_id = _normalize_dashboard_id(dashboard_id)
    if dashboard_id in allowed or normalized_id in allowed:
        return True
    for token in allowed:
        norm_token = _normalize_dashboard_id(token)
        if norm_token and normalized_id.startswith(norm_token):
            return True
    return False


def _require_dashboard_access(user, dashboard_tenant_id: str) -> None:
    if _is_admin_only_dashboard(dashboard_tenant_id) and getattr(user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Dashboard is admin-only")
    allowed = _get_allowed_dashboard_ids(user)
    if not _is_dashboard_allowed(allowed, dashboard_tenant_id):
        raise HTTPException(status_code=403, detail="Dashboard is not available for this tenant")


# =============================================================================
# TENANT DISCOVERY ENDPOINTS
# =============================================================================

@router.get("/tenants", response_model=AvailableTenantDashboards)
async def get_available_dashboards(user=Depends(get_verified_user)):
    """Get list of available tenant dashboards"""
    try:
        tenants = await timestream.get_available_tenants()
        allowed = _get_allowed_dashboard_ids(user)
        if allowed is not None:
            tenants = [t for t in tenants if _is_dashboard_allowed(allowed, t.get("id") or "")]
        if getattr(user, "role", None) != "admin":
            tenants = [t for t in tenants if not _is_admin_only_dashboard(t.get("id") or "")]

        group_map = {}
        if getattr(user, "role", None) == "admin":
            for tenant in Tenants.get_tenants():
                group_name = getattr(tenant, "tenant_group_name", None)
                if not group_name:
                    continue
                for candidate in _candidate_dashboard_ids_from_tenant(tenant):
                    normalized = _normalize_dashboard_id(candidate)
                    if candidate and candidate not in group_map:
                        group_map[candidate] = group_name
                    if normalized and normalized not in group_map:
                        group_map[normalized] = group_name

        for tenant in tenants:
            tenant_id = tenant.get("id") or ""
            group_name = group_map.get(tenant_id) or group_map.get(_normalize_dashboard_id(tenant_id))
            if group_name:
                tenant["tenant_group_name"] = group_name

        return AvailableTenantDashboards(
            tenants=[TenantDashboardInfo(**t) for t in tenants]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get available dashboards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/config", response_model=TenantDashboardConfig)
async def get_tenant_config(tenant_id: str, user=Depends(get_verified_user)):
    """Get configuration for a specific tenant dashboard"""
    _require_dashboard_access(user, tenant_id)
    try:
        config = await timestream.get_tenant_config(tenant_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"Tenant dashboard not found: {tenant_id}")
        return TenantDashboardConfig(**config)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tenant config for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# OVERVIEW ENDPOINTS
# =============================================================================

@router.get("/tenants/{tenant_id}/overview", response_model=OverviewResponse)
async def get_overview(
    tenant_id: str,
    days: int = Query(default=7, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=168),
    shift_filter: Optional[str] = Query(default=None),
    user=Depends(get_verified_user)
):
    """Get overview DPMO metrics for all lines of a tenant"""
    _require_dashboard_access(user, tenant_id)
    try:
        metrics = await timestream.get_overview_metrics(
            tenant_id=tenant_id,
            days=days,
            range_hours=range_hours,
            shift_filter=shift_filter,
        )
        period_days = days
        if range_hours:
            period_days = max(1, (range_hours + 23) // 24)
        return OverviewResponse(
            tenant_id=tenant_id,
            metrics=[OverviewMetric(**m) for m in metrics],
            period_days=period_days,
        )
    except Exception as e:
        logger.error(f"Failed to get overview metrics for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# LINE-SPECIFIC ENDPOINTS
# =============================================================================

@router.get("/tenants/{tenant_id}/lines/{line_id}/metrics", response_model=LineMetrics)
async def get_line_metrics(
    tenant_id: str,
    line_id: str,
    system: str = Query(default="uvbc"),
    days: int = Query(default=7, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=168),
    shift_filter: Optional[str] = Query(default=None),
    user=Depends(get_verified_user)
):
    """Get detailed metrics for a specific line"""
    _require_dashboard_access(user, tenant_id)
    try:
        metrics = await timestream.get_line_metrics(
            tenant_id=tenant_id,
            line_id=line_id,
            system=system,
            days=days,
            range_hours=range_hours,
            shift_filter=shift_filter,
        )
        if "error" in metrics:
            raise HTTPException(status_code=400, detail=metrics["error"])
        return LineMetrics(**metrics)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get line metrics for {tenant_id}/{line_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/lines/{line_id}/incidents", response_model=IncidentsResponse)
async def get_line_incidents(
    tenant_id: str,
    line_id: str,
    system: str = Query(default="washer"),
    limit: int = Query(default=50, ge=1, le=200),
    large_only: bool = Query(default=False),
    days: int = Query(default=7, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=168),
    shift_filter: Optional[str] = Query(default=None),
    user=Depends(get_verified_user)
):
    """Get incident records for a line"""
    _require_dashboard_access(user, tenant_id)
    try:
        incidents = await timestream.get_incidents(
            tenant_id=tenant_id,
            line_id=line_id,
            system=system,
            limit=limit,
            large_only=large_only,
            days=days,
            range_hours=range_hours,
            shift_filter=shift_filter,
        )
        return IncidentsResponse(
            tenant_id=tenant_id,
            line_id=line_id,
            incidents=[Incident(**i) for i in incidents],
            total=len(incidents),
        )
    except Exception as e:
        logger.error(f"Failed to get incidents for {tenant_id}/{line_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/lines/{line_id}/timeseries", response_model=TimeSeriesResponse)
async def get_line_timeseries(
    tenant_id: str,
    line_id: str,
    metric: str = Query(default="down"),
    system: str = Query(default="uvbc"),
    days: int = Query(default=14, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    shift_filter: Optional[str] = Query(default=None),
    user=Depends(get_verified_user)
):
    """Get time series data for charting"""
    _require_dashboard_access(user, tenant_id)
    try:
        data = await timestream.get_time_series(
            tenant_id=tenant_id,
            line_id=line_id,
            system=system,
            metric=metric,
            days=days,
            range_hours=range_hours,
            shift_filter=shift_filter,
        )
        period_days = days
        if range_hours:
            period_days = max(1, (range_hours + 23) // 24)
        return TimeSeriesResponse(
            tenant_id=tenant_id,
            line_id=line_id,
            metric=metric,
            data=[TimeSeriesPoint(**d) for d in data],
            period_days=period_days,
        )
    except Exception as e:
        logger.error(f"Failed to get time series for {tenant_id}/{line_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/shift/snapshot", response_model=ShiftSnapshotResponse)
async def get_shift_snapshot(
    tenant_id: str,
    shift_hours: int = Query(default=12, ge=6, le=24),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    days: Optional[int] = Query(default=None, ge=1, le=30),
    exclude_blackout: bool = Query(default=False),
    shift_filter: Optional[str] = Query(default=None),
    user=Depends(get_verified_user),
):
    """Get shift snapshot totals"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_shift_snapshot(
            tenant_id=tenant_id,
            shift_hours=shift_hours,
            exclude_blackout=exclude_blackout,
            range_hours=range_hours,
            days=days,
            shift_filter=shift_filter,
        )
        return ShiftSnapshotResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get shift snapshot for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/shift/throughput", response_model=ShiftThroughputResponse)
async def get_shift_throughput(
    tenant_id: str,
    line_id: str = Query(default=""),
    shift_hours: int = Query(default=12, ge=6, le=24),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    days: Optional[int] = Query(default=None, ge=1, le=30),
    exclude_blackout: bool = Query(default=False),
    shift_filter: Optional[str] = Query(default=None),
    user=Depends(get_verified_user),
):
    """Get shift throughput diff metrics"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_shift_throughput(
            tenant_id=tenant_id,
            line_id=line_id,
            shift_hours=shift_hours,
            exclude_blackout=exclude_blackout,
            range_hours=range_hours,
            days=days,
            shift_filter=shift_filter,
        )
        return ShiftThroughputResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get shift throughput for {tenant_id}/{line_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/shift/down", response_model=ShiftDownResponse)
async def get_shift_down(
    tenant_id: str,
    line_id: str = Query(default=""),
    shift_hours: int = Query(default=12, ge=6, le=24),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    days: Optional[int] = Query(default=None, ge=1, le=30),
    exclude_blackout: bool = Query(default=False),
    shift_filter: Optional[str] = Query(default=None),
    user=Depends(get_verified_user),
):
    """Get shift down totals"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_shift_down(
            tenant_id=tenant_id,
            line_id=line_id,
            shift_hours=shift_hours,
            exclude_blackout=exclude_blackout,
            range_hours=range_hours,
            days=days,
            shift_filter=shift_filter,
        )
        return ShiftDownResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get shift down totals for {tenant_id}/{line_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/shift/timeseries", response_model=ShiftTimeSeriesResponse)
async def get_shift_timeseries(
    tenant_id: str,
    line_id: str = Query(default=""),
    metric: str = Query(default="total"),
    shift_hours: int = Query(default=12, ge=6, le=24),
    bin_minutes: int = Query(default=10, ge=1, le=60),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    days: Optional[int] = Query(default=None, ge=1, le=30),
    exclude_blackout: bool = Query(default=False),
    shift_filter: Optional[str] = Query(default=None),
    user=Depends(get_verified_user),
):
    """Get shift timeseries data"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_shift_timeseries(
            tenant_id=tenant_id,
            line_id=line_id,
            metric=metric,
            shift_hours=shift_hours,
            bin_minutes=bin_minutes,
            exclude_blackout=exclude_blackout,
            range_hours=range_hours,
            days=days,
            shift_filter=shift_filter,
        )
        return ShiftTimeSeriesResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get shift timeseries for {tenant_id}/{line_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/shift/incidents", response_model=ShiftIncidentsResponse)
async def get_shift_incidents(
    tenant_id: str,
    line_id: str = Query(default=""),
    range_hours: Optional[int] = Query(default=None, ge=1, le=168),
    days: Optional[int] = Query(default=None, ge=1, le=60),
    limit: int = Query(default=50, ge=1, le=200),
    exclude_blackout: bool = Query(default=False),
    shift_filter: Optional[str] = Query(default=None),
    user=Depends(get_verified_user),
):
    """Get shift incidents"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_shift_incidents(
            tenant_id=tenant_id,
            line_id=line_id,
            range_hours=range_hours,
            days=days,
            limit=limit,
            exclude_blackout=exclude_blackout,
            shift_filter=shift_filter,
        )
        incidents = [Incident(**i) for i in result.get("incidents", [])]
        return ShiftIncidentsResponse(
            tenant_id=tenant_id,
            line_id=line_id,
            incidents=incidents,
            total=len(incidents),
        )
    except Exception as e:
        logger.error(f"Failed to get shift incidents for {tenant_id}/{line_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/case-inspection/snapshot", response_model=CaseInspectionSnapshotResponse)
async def get_case_inspection_snapshot(
    tenant_id: str,
    days: int = Query(default=7, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    user=Depends(get_verified_user),
):
    """Get case inspection facility snapshot"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_case_inspection_snapshot(
            tenant_id=tenant_id,
            days=days,
            range_hours=range_hours,
        )
        return CaseInspectionSnapshotResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get case inspection snapshot for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/case-inspection/throughput", response_model=CaseInspectionThroughputResponse)
async def get_case_inspection_throughput(
    tenant_id: str,
    shop_id: str = Query(default="Shop 2"),
    days: int = Query(default=7, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    user=Depends(get_verified_user),
):
    """Get case inspection throughput totals + trend"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_case_inspection_throughput(
            tenant_id=tenant_id,
            shop_id=shop_id,
            days=days,
            range_hours=range_hours,
        )
        return CaseInspectionThroughputResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get case inspection throughput for {tenant_id}/{shop_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/case-inspection/defects", response_model=CaseInspectionDefectsResponse)
async def get_case_inspection_defects(
    tenant_id: str,
    shop_id: str = Query(default="Shop 2"),
    days: int = Query(default=7, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    user=Depends(get_verified_user),
):
    """Get case inspection defect totals + trend"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_case_inspection_defects(
            tenant_id=tenant_id,
            shop_id=shop_id,
            days=days,
            range_hours=range_hours,
        )
        return CaseInspectionDefectsResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get case inspection defects for {tenant_id}/{shop_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/case-inspection/incidents", response_model=CaseInspectionIncidentsResponse)
async def get_case_inspection_incidents(
    tenant_id: str,
    shop_id: str = Query(default="Shop 2"),
    days: int = Query(default=7, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    limit: int = Query(default=10, ge=1, le=50),
    user=Depends(get_verified_user),
):
    """Get case inspection incidents"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_case_inspection_incidents(
            tenant_id=tenant_id,
            shop_id=shop_id,
            days=days,
            limit=limit,
            range_hours=range_hours,
        )
        incidents = [Incident(**i) for i in result.get("incidents", [])]
        return CaseInspectionIncidentsResponse(
            tenant_id=tenant_id,
            shop_id=shop_id,
            period_days=result.get("period_days", days),
            incidents=incidents,
            total=len(incidents),
        )
    except Exception as e:
        logger.error(f"Failed to get case inspection incidents for {tenant_id}/{shop_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/lehr/snapshot", response_model=LehrSnapshotResponse)
async def get_lehr_snapshot(
    tenant_id: str,
    days: int = Query(default=7, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    user=Depends(get_verified_user),
):
    """Get Lehr inspection snapshot"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_lehr_snapshot(
            tenant_id=tenant_id,
            days=days,
            range_hours=range_hours,
        )
        return LehrSnapshotResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get Lehr snapshot for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/lehr/overhead", response_model=LehrMetricsResponse)
async def get_lehr_overhead(
    tenant_id: str,
    days: int = Query(default=7, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    limit: int = Query(default=1000, ge=100, le=5000),
    user=Depends(get_verified_user),
):
    """Get Lehr overhead metrics"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_lehr_overhead(
            tenant_id=tenant_id,
            days=days,
            range_hours=range_hours,
            limit=limit,
        )
        return LehrMetricsResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get Lehr overhead metrics for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/lehr/exit", response_model=LehrMetricsResponse)
async def get_lehr_exit(
    tenant_id: str,
    days: int = Query(default=7, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    limit: int = Query(default=1000, ge=100, le=5000),
    user=Depends(get_verified_user),
):
    """Get Lehr exit metrics"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_lehr_exit(
            tenant_id=tenant_id,
            days=days,
            range_hours=range_hours,
            limit=limit,
        )
        return LehrMetricsResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get Lehr exit metrics for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/lehr/dump-gate", response_model=LehrDumpGateResponse)
async def get_lehr_dump_gate(
    tenant_id: str,
    days: int = Query(default=7, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    user=Depends(get_verified_user),
):
    """Get Lehr dump gate metrics"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_lehr_dump_gate(
            tenant_id=tenant_id,
            days=days,
            range_hours=range_hours,
        )
        return LehrDumpGateResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get Lehr dump gate metrics for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/lehr/incidents", response_model=LehrIncidentsResponse)
async def get_lehr_incidents(
    tenant_id: str,
    days: int = Query(default=7, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    limit: int = Query(default=30, ge=1, le=200),
    user=Depends(get_verified_user),
):
    """Get Lehr incident images"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_lehr_incidents(
            tenant_id=tenant_id,
            days=days,
            range_hours=range_hours,
            limit=limit,
        )
        incidents = [Incident(**i) for i in result.get("incidents", [])]
        return LehrIncidentsResponse(
            tenant_id=tenant_id,
            period_days=result.get("period_days", days),
            range_hours=result.get("range_hours"),
            incidents=incidents,
            total=len(incidents),
        )
    except Exception as e:
        logger.error(f"Failed to get Lehr incidents for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/finalcheck/snapshot", response_model=FinalCheckSnapshotResponse)
async def get_finalcheck_snapshot(
    tenant_id: str,
    line_id: str = Query(default="CX"),
    days: int = Query(default=7, ge=1, le=60),
    range_hours: Optional[int] = Query(default=None, ge=1, le=168),
    user=Depends(get_verified_user),
):
    """Get FinalCheck snapshot counts"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_finalcheck_snapshot(
            tenant_id=tenant_id,
            line_id=line_id,
            days=days,
            range_hours=range_hours,
        )
        return FinalCheckSnapshotResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get FinalCheck snapshot for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/finalcheck/defects", response_model=FinalCheckDefectsResponse)
async def get_finalcheck_defects(
    tenant_id: str,
    line_id: str = Query(default="CX"),
    days: int = Query(default=7, ge=1, le=60),
    range_hours: Optional[int] = Query(default=None, ge=1, le=168),
    limit: int = Query(default=9, ge=1, le=20),
    user=Depends(get_verified_user),
):
    """Get FinalCheck defect chart data"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_finalcheck_defects(
            tenant_id=tenant_id,
            line_id=line_id,
            days=days,
            range_hours=range_hours,
            limit=limit,
        )
        return FinalCheckDefectsResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get FinalCheck defects for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/finalcheck/incidents", response_model=FinalCheckIncidentsResponse)
async def get_finalcheck_incidents(
    tenant_id: str,
    line_id: str = Query(default="CX"),
    days: int = Query(default=7, ge=1, le=60),
    range_hours: Optional[int] = Query(default=None, ge=1, le=168),
    limit: int = Query(default=30, ge=1, le=200),
    user=Depends(get_verified_user),
):
    """Get FinalCheck incident images"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_finalcheck_incidents(
            tenant_id=tenant_id,
            line_id=line_id,
            days=days,
            range_hours=range_hours,
            limit=limit,
        )
        incidents = result.get("incidents", [])
        return FinalCheckIncidentsResponse(
            tenant_id=tenant_id,
            line_id=line_id,
            incidents=incidents,
            total=len(incidents),
        )
    except Exception as e:
        logger.error(f"Failed to get FinalCheck incidents for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/sidewall/snapshot", response_model=SidewallSnapshotResponse)
async def get_sidewall_snapshot(
    tenant_id: str,
    days: int = Query(default=7, ge=1, le=60),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    user=Depends(get_verified_user),
):
    """Get sidewall snapshot totals"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_sidewall_snapshot(
            tenant_id=tenant_id,
            days=days,
            range_hours=range_hours,
        )
        return SidewallSnapshotResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get sidewall snapshot for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/sidewall/inspections", response_model=SidewallInspectionsResponse)
async def get_sidewall_inspections(
    tenant_id: str,
    days: int = Query(default=7, ge=1, le=60),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    user=Depends(get_verified_user),
):
    """Get sidewall inspections overview"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_sidewall_inspections(
            tenant_id=tenant_id,
            days=days,
            range_hours=range_hours,
        )
        return SidewallInspectionsResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get sidewall inspections for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/sidewall/defect", response_model=SidewallDefectResponse)
async def get_sidewall_defect(
    tenant_id: str,
    defect_class: str = Query(default="critical"),
    days: int = Query(default=7, ge=1, le=60),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    user=Depends(get_verified_user),
):
    """Get sidewall defect totals + trend"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_sidewall_defect(
            tenant_id=tenant_id,
            defect_class=defect_class,
            days=days,
            range_hours=range_hours,
        )
        return SidewallDefectResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get sidewall defect for {tenant_id}/{defect_class}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/sidewall/incidents", response_model=SidewallIncidentsResponse)
async def get_sidewall_incidents(
    tenant_id: str,
    defect_class: str = Query(default="critical"),
    days: int = Query(default=7, ge=1, le=60),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    limit: int = Query(default=10, ge=1, le=50),
    user=Depends(get_verified_user),
):
    """Get sidewall incidents"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_sidewall_incidents(
            tenant_id=tenant_id,
            defect_class=defect_class,
            days=days,
            limit=limit,
            range_hours=range_hours,
        )
        incidents = [Incident(**i) for i in result.get("incidents", [])]
        return SidewallIncidentsResponse(
            tenant_id=tenant_id,
            defect_class=defect_class,
            period_days=result.get("period_days", days),
            incidents=incidents,
            total=len(incidents),
        )
    except Exception as e:
        logger.error(f"Failed to get sidewall incidents for {tenant_id}/{defect_class}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/sidewall/health", response_model=SystemHealthResponse)
async def get_sidewall_health(
    tenant_id: str,
    minutes: int = Query(default=30, ge=1, le=120),
    camera_days: int = Query(default=7, ge=1, le=30),
    user=Depends(get_verified_user),
):
    """Get sidewall system health"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_sidewall_health(
            tenant_id=tenant_id,
            minutes=minutes,
            camera_days=camera_days,
        )
        devices = [DeviceHealth(**d) for d in result.get("devices", [])]
        return SystemHealthResponse(
            tenant_id=tenant_id,
            devices=devices,
            timestamp=result.get("timestamp", ""),
        )
    except Exception as e:
        logger.error(f"Failed to get sidewall health for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/scale/snapshot", response_model=ScaleSnapshotResponse)
async def get_scale_snapshot(
    tenant_id: str,
    days: int = Query(default=7, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    user=Depends(get_verified_user),
):
    """Get scale snapshot totals"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_scale_snapshot(
            tenant_id=tenant_id,
            days=days,
            range_hours=range_hours,
        )
        return ScaleSnapshotResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get scale snapshot for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/scale/overview", response_model=ScaleOverviewResponse)
async def get_scale_overview(
    tenant_id: str,
    system_id: str = Query(default="WW1"),
    days: int = Query(default=7, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    user=Depends(get_verified_user),
):
    """Get scale overview data"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_scale_overview(
            tenant_id=tenant_id,
            system_id=system_id,
            days=days,
            range_hours=range_hours,
        )
        return ScaleOverviewResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get scale overview for {tenant_id}/{system_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/scale/bay-metrics", response_model=ScaleBayMetricsResponse)
async def get_scale_bay_metrics(
    tenant_id: str,
    system_id: str = Query(default="WW1"),
    bay: int = Query(default=1, ge=1, le=2),
    days: int = Query(default=7, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    user=Depends(get_verified_user),
):
    """Get scale bay metrics"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_scale_bay_metrics(
            tenant_id=tenant_id,
            system_id=system_id,
            bay=bay,
            days=days,
            range_hours=range_hours,
        )
        return ScaleBayMetricsResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get scale bay metrics for {tenant_id}/{system_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/scale/bay-table", response_model=ScaleBayTableResponse)
async def get_scale_bay_table(
    tenant_id: str,
    system_id: str = Query(default="WW1"),
    bay: int = Query(default=1, ge=1, le=2),
    days: int = Query(default=7, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    limit: int = Query(default=50, ge=10, le=500),
    user=Depends(get_verified_user),
):
    """Get scale bay table rows"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_scale_bay_table(
            tenant_id=tenant_id,
            system_id=system_id,
            bay=bay,
            days=days,
            range_hours=range_hours,
            limit=limit,
        )
        return ScaleBayTableResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get scale bay table for {tenant_id}/{system_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/scale/bin-images", response_model=ScaleBinImagesResponse)
async def get_scale_bin_images(
    tenant_id: str,
    system_id: str = Query(default="WW1"),
    bay: int = Query(default=1, ge=1, le=2),
    days: int = Query(default=7, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    limit: int = Query(default=15, ge=1, le=100),
    user=Depends(get_verified_user),
):
    """Get scale bin images"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_scale_bin_images(
            tenant_id=tenant_id,
            system_id=system_id,
            bay=bay,
            days=days,
            range_hours=range_hours,
            limit=limit,
        )
        return ScaleBinImagesResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get scale bin images for {tenant_id}/{system_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/scale/camera-health", response_model=ScaleCameraHealthResponse)
async def get_scale_camera_health(
    tenant_id: str,
    system_id: str = Query(default="WW1"),
    days: int = Query(default=7, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    limit: int = Query(default=50, ge=10, le=500),
    user=Depends(get_verified_user),
):
    """Get scale camera health"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_scale_camera_health(
            tenant_id=tenant_id,
            system_id=system_id,
            days=days,
            range_hours=range_hours,
            limit=limit,
        )
        return ScaleCameraHealthResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get scale camera health for {tenant_id}/{system_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/lines/{line_id}/orientation", response_model=OrientationResponse)
async def get_line_orientation(
    tenant_id: str,
    line_id: str,
    system: str = Query(default="washer"),
    defect_type: str = Query(default="down"),
    days: int = Query(default=7, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    bin_size: int = Query(default=100, ge=10, le=500),
    shift_filter: Optional[str] = Query(default=None),
    user=Depends(get_verified_user)
):
    """Get defect location distribution (x-position histogram)"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_orientation_data(
            tenant_id=tenant_id,
            line_id=line_id,
            system=system,
            defect_type=defect_type,
            days=days,
            bin_size=bin_size,
            range_hours=range_hours,
            shift_filter=shift_filter,
        )
        return OrientationResponse(
            tenant_id=tenant_id,
            line_id=line_id,
            system=system,
            defect_type=result.get("defect_type", defect_type),
            bin_size=result.get("bin_size", bin_size),
            data=[OrientationBin(**d) for d in result.get("data", [])],
        )
    except Exception as e:
        logger.error(f"Failed to get orientation for {tenant_id}/{line_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# UVBC-SPECIFIC ENDPOINTS
# =============================================================================

@router.get("/tenants/{tenant_id}/uvbc/{line_id}/intensity", response_model=IntensityResponse)
async def get_uvbc_intensity(
    tenant_id: str,
    line_id: str,
    days: int = Query(default=7, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    shift_filter: Optional[str] = Query(default=None),
    user=Depends(get_verified_user)
):
    """Get UVBC ring intensity data for a line"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_uvbc_intensity(
            tenant_id=tenant_id,
            line_id=line_id,
            days=days,
            range_hours=range_hours,
            shift_filter=shift_filter,
        )
        intensity_data = result.get("data", [])
        return IntensityResponse(
            tenant_id=tenant_id,
            line_id=line_id,
            data=[IntensityStats(**d) for d in intensity_data],
        )
    except Exception as e:
        logger.error(f"Failed to get UVBC intensity for {tenant_id}/{line_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/uvbc/{line_id}/partials", response_model=PartialRingResponse)
async def get_partial_ring_data(
    tenant_id: str,
    line_id: str,
    days: int = Query(default=7, ge=1, le=30),
    range_hours: Optional[int] = Query(default=None, ge=1, le=720),
    shift_filter: Optional[str] = Query(default=None),
    user=Depends(get_verified_user)
):
    """Get partial ring percentage distribution"""
    _require_dashboard_access(user, tenant_id)
    try:
        data = await timestream.get_partial_ring_data(
            tenant_id=tenant_id,
            line_id=line_id,
            days=days,
            range_hours=range_hours,
            shift_filter=shift_filter,
        )
        return PartialRingResponse(
            tenant_id=tenant_id,
            line_id=line_id,
            data=[PartialRingData(**d) for d in data],
        )
    except Exception as e:
        logger.error(f"Failed to get partial ring data for {tenant_id}/{line_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@router.get("/tenants/{tenant_id}/incidents/{uuid}/image-url", response_model=ImageUrlResponse)
async def get_incident_image_url(
    tenant_id: str,
    uuid: str,
    user=Depends(get_verified_user)
):
    """Get image URL for an incident"""
    _require_dashboard_access(user, tenant_id)
    if not uuid:
        raise HTTPException(status_code=400, detail="UUID is required")

    try:
        image_url = await timestream.generate_incident_image_url(tenant_id=tenant_id, uuid=uuid)
        if not image_url:
            raise HTTPException(status_code=404, detail="Image not found")
        return ImageUrlResponse(tenant_id=tenant_id, uuid=uuid, image_url=image_url)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get image URL for {uuid}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear", response_model=CacheClearResponse)
async def clear_cache(user=Depends(get_admin_user)):
    """Clear all dashboard caches (admin only)"""
    try:
        await timestream.clear_cache()
        return CacheClearResponse(status="ok", message="Cache cleared successfully")
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SYSTEM HEALTH ENDPOINTS
# =============================================================================

@router.get("/tenants/{tenant_id}/health", response_model=SystemHealthResponse)
async def get_system_health(
    tenant_id: str,
    minutes: int = Query(default=30, ge=5, le=120),
    user=Depends(get_verified_user)
):
    """Get system health status for all devices of a tenant"""
    _require_dashboard_access(user, tenant_id)
    try:
        result = await timestream.get_system_health(tenant_id=tenant_id, minutes=minutes)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return SystemHealthResponse(
            tenant_id=tenant_id,
            devices=[DeviceHealth(**d) for d in result.get("devices", [])],
            timestamp=result.get("timestamp", "")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get system health for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
