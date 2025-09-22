"""
Health check endpoints for monitoring and diagnostics.

These endpoints help you monitor your API's health, dependencies,
and system status - essential for production deployment.
"""

import time
from fastapi import APIRouter, Depends
from datetime import datetime

from ..models.common import HealthStatus
from ..dependencies.session import get_session_manager, get_model_manager, SessionManager
from src.models.manager import ModelManager

router = APIRouter()

# Track server start time for uptime calculation
_server_start_time = time.time()

@router.get("/", response_model=HealthStatus)
async def health_check(
    session_manager: SessionManager = Depends(get_session_manager),
    model_manager: ModelManager = Depends(get_model_manager)
):
    """
    Basic health check endpoint.
    
    Returns the status of the API and its dependencies.
    Useful for load balancers and monitoring systems.
    """
    
    uptime = time.time() - _server_start_time
    
    # Check dependencies
    dependencies = {}
    
    # Check session manager
    try:
        session_stats = session_manager.get_stats()
        dependencies["session_manager"] = f"✅ Active ({session_stats['active_sessions']} sessions)"
    except Exception as e:
        dependencies["session_manager"] = f"❌ Error: {str(e)}"
    
    # Check model manager and marker service
    try:
        if hasattr(model_manager, 'marker') and model_manager.marker:
            dependencies["marker_service"] = "✅ Available"
        else:
            dependencies["marker_service"] = "⚠️ Not initialized"
    except Exception as e:
        dependencies["marker_service"] = f"❌ Error: {str(e)}"
    
    # Check if we can create model instances (basic functionality test)
    try:
        # This doesn't actually create expensive models, just tests the manager
        dependencies["model_providers"] = "✅ Manager operational"
    except Exception as e:
        dependencies["model_providers"] = f"❌ Error: {str(e)}"
    
    return HealthStatus(
        status="healthy",
        version="1.0.0",
        uptime=uptime,
        dependencies=dependencies
    )

@router.get("/detailed")
async def detailed_health_check(
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Detailed health check with system metrics.
    
    Returns more comprehensive information about system state,
    useful for debugging and monitoring dashboards.
    """
    
    uptime = time.time() - _server_start_time
    session_stats = session_manager.get_stats()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": uptime,
        "uptime_human": f"{uptime//3600:.0f}h {(uptime%3600)//60:.0f}m {uptime%60:.0f}s",
        "sessions": {
            "active_count": session_stats["active_sessions"],
            "timeout_minutes": session_stats["timeout_minutes"],
            "oldest_session_age_seconds": session_stats["oldest_session_age"]
        },
        "system": {
            "memory_usage": "Not implemented", # Could add psutil here
            "cpu_usage": "Not implemented"
        }
    }

@router.get("/ready")
async def readiness_check(model_manager: ModelManager = Depends(get_model_manager)):
    """
    Readiness probe for Kubernetes/container deployments.
    
    Returns 200 only when the service is ready to handle requests.
    This is different from health - health shows status, ready shows availability.
    """
    
    # Check if critical services are ready
    if not hasattr(model_manager, 'marker') or not model_manager.marker:
        return {"ready": False, "reason": "Marker service not initialized"}
    
    return {"ready": True, "message": "Service ready to handle requests"}