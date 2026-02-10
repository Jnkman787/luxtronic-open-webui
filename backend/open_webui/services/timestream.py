"""
Dashboard Data Service
Proxies requests to the rag-platform backend for tenant dashboard data.
All sensitive Timestream queries and tenant configurations are handled by rag-platform.
"""

import os
import logging
import aiohttp
import json
import asyncio
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# RAG Platform endpoint - configured via environment
RAG_PLATFORM_URL = os.getenv(
    "RAG_PLATFORM_URL",
    "http://localhost:9000/2015-03-31/functions/function/invocations",
)
RAG_PLATFORM_API_KEY = os.getenv("RAG_MASTER_API_KEY", "")

# The AWS Lambda runtime container only processes one invocation at a time. The
# local emulator can crash if it receives overlapping requests, so we serialize
# calls through a single async lock.
_rag_platform_lock = asyncio.Lock()


async def _invoke_rag_platform(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invoke the rag-platform Lambda for dashboard data.

    Args:
        action: The dashboard action to perform (e.g., "dashboard_overview", "dashboard_line_metrics")
        params: Parameters for the action

    Returns:
        Response data from rag-platform
    """
    payload = {
        "action": action,
        "params": params
    }

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            async with _rag_platform_lock:
                async with aiohttp.ClientSession() as session:
                    headers = {"Content-Type": "application/json"}
                    if RAG_PLATFORM_API_KEY:
                        headers["x-api-key"] = RAG_PLATFORM_API_KEY

                    async with session.post(
                        RAG_PLATFORM_URL,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"Rag-platform error: {response.status} - {error_text}")
                            raise Exception(f"Rag-platform returned {response.status}")

                        raw_text = await response.text()
                        try:
                            result = json.loads(raw_text)
                        except json.JSONDecodeError as e:
                            logger.error(
                                "Failed to decode rag-platform response as JSON: "
                                f"status={response.status} content_type={response.headers.get('Content-Type')} "
                                f"error={e} body_prefix={raw_text[:500]!r}"
                            )
                            raise Exception("Dashboard backend returned invalid JSON") from e

                        # Handle Lambda response format (may have statusCode/body wrapper)
                        if isinstance(result, dict) and "statusCode" in result:
                            if result.get("statusCode") != 200:
                                raise Exception(
                                    f"Lambda returned status {result.get('statusCode')}: {result.get('body')}"
                                )
                            body = result.get("body", "{}")
                            if isinstance(body, str):
                                return json.loads(body)
                            return body

                        return result
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            last_error = e
            if attempt < 2:
                await asyncio.sleep(0.25 * (2**attempt))
                continue
            logger.error(f"Failed to connect to rag-platform: {e}")
            raise Exception(f"Failed to connect to dashboard backend: {str(e)}") from e

    raise Exception(f"Failed to connect to dashboard backend: {last_error}")


async def get_available_tenants() -> List[Dict[str, str]]:
    """Get list of available tenant dashboards"""
    result = await _invoke_rag_platform("dashboard_get_tenants", {})
    return result.get("tenants", [])


async def get_tenant_config(tenant_id: str) -> Optional[Dict[str, Any]]:
    """Get dashboard configuration for a tenant"""
    result = await _invoke_rag_platform("dashboard_get_config", {"tenant_id": tenant_id})
    return result.get("config")


async def get_overview_metrics(
    tenant_id: str,
    days: int = 7,
    range_hours: Optional[int] = None,
    shift_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get overview DPMO metrics for all lines of a tenant"""
    params: Dict[str, Any] = {"tenant_id": tenant_id, "days": days}
    if range_hours:
        params["range_hours"] = range_hours
    if shift_filter:
        params["shift_filter"] = shift_filter
    result = await _invoke_rag_platform("dashboard_overview", params)
    return result.get("metrics", [])


async def get_line_metrics(
    tenant_id: str,
    line_id: str,
    system: str = "uvbc",
    days: int = 7,
    range_hours: Optional[int] = None,
    shift_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """Get detailed metrics for a specific line"""
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "line_id": line_id,
        "system": system,
        "days": days,
    }
    if range_hours:
        params["range_hours"] = range_hours
    if shift_filter:
        params["shift_filter"] = shift_filter
    result = await _invoke_rag_platform("dashboard_line_metrics", params)
    return result.get("metrics", {})


async def get_incidents(
    tenant_id: str,
    line_id: str,
    system: str = "washer",
    limit: int = 50,
    large_only: bool = False,
    days: int = 7,
    range_hours: Optional[int] = None,
    shift_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get incident records for a line"""
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "line_id": line_id,
        "system": system,
        "limit": limit,
        "large_only": large_only,
        "days": days,
    }
    if range_hours:
        params["range_hours"] = range_hours
    if shift_filter:
        params["shift_filter"] = shift_filter
    result = await _invoke_rag_platform("dashboard_incidents", params)
    return result.get("incidents", [])


async def get_case_inspection_snapshot(
    tenant_id: str,
    days: int = 7,
    range_hours: Optional[int] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {"tenant_id": tenant_id, "days": days}
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_case_inspection_snapshot", params)
    return result


async def get_case_inspection_throughput(
    tenant_id: str,
    shop_id: str,
    days: int = 7,
    range_hours: Optional[int] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "shop_id": shop_id,
        "days": days,
    }
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_case_inspection_throughput", params)
    return result


async def get_case_inspection_defects(
    tenant_id: str,
    shop_id: str,
    days: int = 7,
    range_hours: Optional[int] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "shop_id": shop_id,
        "days": days,
    }
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_case_inspection_defects", params)
    return result


async def get_case_inspection_incidents(
    tenant_id: str,
    shop_id: str,
    days: int = 7,
    limit: int = 10,
    range_hours: Optional[int] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "shop_id": shop_id,
        "days": days,
        "limit": limit,
    }
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_case_inspection_incidents", params)
    return result


async def get_lehr_snapshot(
    tenant_id: str,
    days: int = 7,
    range_hours: Optional[int] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {"tenant_id": tenant_id, "days": days}
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_lehr_snapshot", params)
    return result


async def get_lehr_overhead(
    tenant_id: str,
    days: int = 7,
    range_hours: Optional[int] = None,
    limit: int = 1000,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {"tenant_id": tenant_id, "days": days, "limit": limit}
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_lehr_overhead", params)
    return result


async def get_lehr_exit(
    tenant_id: str,
    days: int = 7,
    range_hours: Optional[int] = None,
    limit: int = 1000,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {"tenant_id": tenant_id, "days": days, "limit": limit}
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_lehr_exit", params)
    return result


async def get_lehr_dump_gate(
    tenant_id: str,
    days: int = 7,
    range_hours: Optional[int] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {"tenant_id": tenant_id, "days": days}
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_lehr_dump_gate", params)
    return result


async def get_lehr_incidents(
    tenant_id: str,
    days: int = 7,
    range_hours: Optional[int] = None,
    limit: int = 30,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {"tenant_id": tenant_id, "days": days, "limit": limit}
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_lehr_incidents", params)
    return result


async def get_finalcheck_snapshot(
    tenant_id: str,
    line_id: str,
    days: int = 7,
    range_hours: Optional[int] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {"tenant_id": tenant_id, "line_id": line_id, "days": days}
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_finalcheck_snapshot", params)
    return result


async def get_finalcheck_defects(
    tenant_id: str,
    line_id: str,
    days: int = 7,
    range_hours: Optional[int] = None,
    limit: int = 9,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "line_id": line_id,
        "days": days,
        "limit": limit,
    }
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_finalcheck_defects", params)
    return result


async def get_finalcheck_incidents(
    tenant_id: str,
    line_id: str,
    days: int = 7,
    range_hours: Optional[int] = None,
    limit: int = 30,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "line_id": line_id,
        "days": days,
        "limit": limit,
    }
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_finalcheck_incidents", params)
    return result


async def get_sidewall_snapshot(
    tenant_id: str,
    days: int = 7,
    range_hours: Optional[int] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {"tenant_id": tenant_id, "days": days}
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_sidewall_snapshot", params)
    return result


async def get_sidewall_inspections(
    tenant_id: str,
    days: int = 7,
    range_hours: Optional[int] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {"tenant_id": tenant_id, "days": days}
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_sidewall_inspections", params)
    return result


async def get_sidewall_defect(
    tenant_id: str,
    defect_class: str,
    days: int = 7,
    range_hours: Optional[int] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "defect_class": defect_class,
        "days": days,
    }
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_sidewall_defect", params)
    return result


async def get_sidewall_incidents(
    tenant_id: str,
    defect_class: str,
    days: int = 7,
    limit: int = 10,
    range_hours: Optional[int] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "defect_class": defect_class,
        "days": days,
        "limit": limit,
    }
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_sidewall_incidents", params)
    return result


async def get_sidewall_health(
    tenant_id: str,
    minutes: int = 30,
    camera_days: int = 7,
) -> Dict[str, Any]:
    result = await _invoke_rag_platform("dashboard_sidewall_health", {
        "tenant_id": tenant_id,
        "minutes": minutes,
        "camera_days": camera_days,
    })
    return result


async def get_scale_snapshot(
    tenant_id: str,
    days: int = 7,
    range_hours: Optional[int] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {"tenant_id": tenant_id, "days": days}
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_scale_snapshot", params)
    return result


async def get_scale_overview(
    tenant_id: str,
    system_id: str,
    days: int = 7,
    range_hours: Optional[int] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "system_id": system_id,
        "days": days,
    }
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_scale_overview", params)
    return result


async def get_scale_bay_metrics(
    tenant_id: str,
    system_id: str,
    bay: int,
    days: int = 7,
    range_hours: Optional[int] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "system_id": system_id,
        "bay": bay,
        "days": days,
    }
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_scale_bay_metrics", params)
    return result


async def get_scale_bay_table(
    tenant_id: str,
    system_id: str,
    bay: int,
    days: int = 7,
    range_hours: Optional[int] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "system_id": system_id,
        "bay": bay,
        "days": days,
        "limit": limit,
    }
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_scale_bay_table", params)
    return result


async def get_scale_bin_images(
    tenant_id: str,
    system_id: str,
    bay: int,
    days: int = 7,
    range_hours: Optional[int] = None,
    limit: int = 15,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "system_id": system_id,
        "bay": bay,
        "days": days,
        "limit": limit,
    }
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_scale_bin_images", params)
    return result


async def get_scale_camera_health(
    tenant_id: str,
    system_id: str,
    days: int = 7,
    range_hours: Optional[int] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "system_id": system_id,
        "days": days,
        "limit": limit,
    }
    if range_hours:
        params["range_hours"] = range_hours
    result = await _invoke_rag_platform("dashboard_scale_camera_health", params)
    return result


async def get_time_series(
    tenant_id: str,
    line_id: str,
    system: str = "uvbc",
    metric: str = "down",
    days: int = 14,
    range_hours: Optional[int] = None,
    shift_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get time series data for charting"""
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "line_id": line_id,
        "system": system,
        "metric": metric,
        "days": days,
    }
    if range_hours:
        params["range_hours"] = range_hours
    if shift_filter:
        params["shift_filter"] = shift_filter
    result = await _invoke_rag_platform("dashboard_timeseries", params)
    return result.get("data", [])


async def get_shift_snapshot(
    tenant_id: str,
    shift_hours: int = 12,
    exclude_blackout: bool = False,
    range_hours: Optional[int] = None,
    days: Optional[int] = None,
    shift_filter: Optional[str] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "shift_hours": shift_hours,
        "exclude_blackout": exclude_blackout,
    }
    if range_hours:
        params["range_hours"] = range_hours
    if days:
        params["days"] = days
    if shift_filter:
        params["shift_filter"] = shift_filter
    result = await _invoke_rag_platform("dashboard_shift_snapshot", params)
    return result


async def get_shift_throughput(
    tenant_id: str,
    line_id: str,
    shift_hours: int = 12,
    exclude_blackout: bool = False,
    range_hours: Optional[int] = None,
    days: Optional[int] = None,
    shift_filter: Optional[str] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "line_id": line_id,
        "shift_hours": shift_hours,
        "exclude_blackout": exclude_blackout,
    }
    if range_hours:
        params["range_hours"] = range_hours
    if days:
        params["days"] = days
    if shift_filter:
        params["shift_filter"] = shift_filter
    result = await _invoke_rag_platform("dashboard_shift_throughput", params)
    return result


async def get_shift_down(
    tenant_id: str,
    line_id: str,
    shift_hours: int = 12,
    exclude_blackout: bool = False,
    range_hours: Optional[int] = None,
    days: Optional[int] = None,
    shift_filter: Optional[str] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "line_id": line_id,
        "shift_hours": shift_hours,
        "exclude_blackout": exclude_blackout,
    }
    if range_hours:
        params["range_hours"] = range_hours
    if days:
        params["days"] = days
    if shift_filter:
        params["shift_filter"] = shift_filter
    result = await _invoke_rag_platform("dashboard_shift_down", params)
    return result


async def get_shift_timeseries(
    tenant_id: str,
    line_id: str,
    metric: str,
    shift_hours: int = 12,
    bin_minutes: int = 10,
    exclude_blackout: bool = False,
    range_hours: Optional[int] = None,
    days: Optional[int] = None,
    shift_filter: Optional[str] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "line_id": line_id,
        "metric": metric,
        "shift_hours": shift_hours,
        "bin_minutes": bin_minutes,
        "exclude_blackout": exclude_blackout,
    }
    if range_hours:
        params["range_hours"] = range_hours
    if days:
        params["days"] = days
    if shift_filter:
        params["shift_filter"] = shift_filter
    result = await _invoke_rag_platform("dashboard_shift_timeseries", params)
    return result


async def get_shift_incidents(
    tenant_id: str,
    line_id: str,
    range_hours: Optional[int] = None,
    days: Optional[int] = None,
    limit: int = 50,
    exclude_blackout: bool = False,
    shift_filter: Optional[str] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "line_id": line_id,
        "limit": limit,
        "exclude_blackout": exclude_blackout,
    }
    if range_hours:
        params["range_hours"] = range_hours
    if days:
        params["days"] = days
    if shift_filter:
        params["shift_filter"] = shift_filter
    result = await _invoke_rag_platform("dashboard_shift_incidents", params)
    return result


async def get_uvbc_intensity(
    tenant_id: str,
    line_id: str,
    days: int = 7,
    mode: str = "daily",
    range_hours: Optional[int] = None,
    shift_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """Get UVBC ring intensity data"""
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "line_id": line_id,
        "days": days,
        "mode": mode,
    }
    if range_hours:
        params["range_hours"] = range_hours
    if shift_filter:
        params["shift_filter"] = shift_filter
    result = await _invoke_rag_platform("dashboard_uvbc_intensity", params)
    return result


async def get_orientation_data(
    tenant_id: str,
    line_id: str,
    system: str = "washer",
    defect_type: str = "down",
    days: int = 7,
    bin_size: int = 100,
    range_hours: Optional[int] = None,
    shift_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """Get defect location distribution (x-position histogram)"""
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "line_id": line_id,
        "system": system,
        "defect_type": defect_type,
        "days": days,
        "bin_size": bin_size,
    }
    if range_hours:
        params["range_hours"] = range_hours
    if shift_filter:
        params["shift_filter"] = shift_filter
    result = await _invoke_rag_platform("dashboard_orientation", params)
    return result


async def get_partial_ring_data(
    tenant_id: str,
    line_id: str,
    days: int = 7,
    range_hours: Optional[int] = None,
    shift_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get partial ring percentage distribution"""
    params: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "line_id": line_id,
        "days": days,
    }
    if range_hours:
        params["range_hours"] = range_hours
    if shift_filter:
        params["shift_filter"] = shift_filter
    result = await _invoke_rag_platform("dashboard_partial_rings", params)
    return result.get("data", [])


async def generate_incident_image_url(tenant_id: str, uuid: str) -> Optional[str]:
    """Generate URL for incident image"""
    result = await _invoke_rag_platform("dashboard_incident_image", {
        "tenant_id": tenant_id,
        "uuid": uuid
    })
    return result.get("image_url")


async def clear_cache() -> None:
    """Clear dashboard caches on rag-platform"""
    await _invoke_rag_platform("dashboard_clear_cache", {})


async def get_system_health(tenant_id: str, minutes: int = 30) -> Dict[str, Any]:
    """Get system health status for all devices of a tenant"""
    result = await _invoke_rag_platform("dashboard_system_health", {
        "tenant_id": tenant_id,
        "minutes": minutes
    })
    return result


async def get_mystuff_chart_data(
    sql_template: str,
    timeframe_type: str,
    timeframe_value: int,
    series_config: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Execute a saved SQL template with the provided timeframe and return chart data.
    Used by My Stuff dashboard to refresh saved charts with different date ranges.

    Args:
        sql_template: SQL with {start_time} and {end_time} placeholders
        timeframe_type: 'days' or 'hours'
        timeframe_value: Number of days or hours
        series_config: List of {column, name, color} dicts where:
            - column: original SQL column name (used for matching)
            - name: display name (user-editable)
            - color: series color

    Returns:
        Dict with labels, series (with colors), and optional error
    """
    payload = {
        "sql_template": sql_template,
        "timeframe_type": timeframe_type,
        "timeframe_value": timeframe_value,
        "series_config": series_config or []
    }
    result = await _invoke_rag_platform("dashboard_mystuff_chart_data", payload)

    # Apply series_config mapping since RAG doesn't handle it
    # Match by column name and apply custom name/color
    if series_config and result.get('series'):
        config_by_column = {c.get('column'): c for c in series_config if c.get('column')}
        for series in result['series']:
            original_name = series.get('name')
            if original_name in config_by_column:
                config = config_by_column[original_name]
                series['name'] = config.get('name', original_name)
                series['color'] = config.get('color', series.get('color'))

    return result
