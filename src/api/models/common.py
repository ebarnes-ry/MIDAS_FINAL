"""
Common API models used across different endpoints.

These models represent shared concepts like errors, pagination, and base responses.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from datetime import datetime

class APIError(BaseModel):
    """Standard error response format."""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Machine-readable error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class APIResponse(BaseModel):
    """Base response wrapper for all API endpoints."""
    success: bool = Field(..., description="Whether the request was successful")
    message: Optional[str] = Field(None, description="Human-readable response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HealthStatus(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    uptime: float = Field(..., description="Uptime in seconds")
    dependencies: Dict[str, str] = Field(..., description="Status of external dependencies")