from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AssessExcavationRiskInput(BaseModel):
    """Input model generated from DOIR action_types inputs."""
    model_config = ConfigDict(extra="forbid")
    project_id: str = Field(description='Construction or excavation project identifier.')
    excavation_area: Dict[str, Any] = Field(description='GeoJSON polygon submitted by the requester.')
    excavation_depth: float = Field(description='Excavation depth in meters.')
    construction_method: str = Field(description='Construction method, for example MECHANICAL or MANUAL.')
    entitlement_id: str = Field(description='Purpose-bound authorization issued by Policy Service.')
    provider_id: str = Field(default='changchun', description='Provider Runtime route for the lifeline domain.')


class AssessExcavationRiskResult(BaseModel):
    """Result model generated from the product output schema."""
    model_config = ConfigDict(extra="allow")
    overall_risk: Optional[str] = None
    affected_asset_types: Optional[List[str]] = None
    affected_segment_count: Optional[float] = None
    recommendations: Optional[List[str]] = None
    quality_summary: Optional[Dict[str, Any]] = None
    receipt_id: Optional[str] = None
    request_id: Optional[str] = None
    policy_decision: Optional[str] = None
    runtime_version: Optional[str] = None
